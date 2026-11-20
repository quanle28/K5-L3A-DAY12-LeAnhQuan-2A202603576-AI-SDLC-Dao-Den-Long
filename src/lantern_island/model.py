"""Ticket-03/v1.2 simulation on the retained 60Hz core. No GUI or wall clock."""
import json
import math
import random
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
from .maps import World
from .validation import DEFAULT_INPUT,number,integer,boolean,fields,position,validate_inputs

DT=1/60
ISLAND_RADIUS=40.
TUNING=json.loads((Path(__file__).resolve().parents[2]/'game.contract.json').read_text(encoding='utf-8'))['tuning']
SHADE_STATES=('spawning','wander','chase','recoil','stunned','drain')


def distance(a,b): return math.hypot(a[0]-b[0],a[2]-b[2])
def rounded(pos): return [round(float(v),3)+0. for v in pos]
def direction(a,b):
    dx,dz=b[0]-a[0],b[2]-a[2]
    d=math.hypot(dx,dz)
    return [dx/d,dz/d] if d>1e-12 else [1.,0.]
def id_key(e):
    identifier=e['id']
    prefix=identifier.rstrip('0123456789')
    suffix=identifier[len(prefix):]
    return prefix,int(suffix) if suffix else -1,identifier


class Game:
    def __init__(self,seed=12,scenario=None,night=1):
        if night not in (1,2,3): raise ValueError('night must be 1, 2 or 3')
        self.night=night
        self.world=World(night)
        self.rng=random.Random(seed)
        self.tick=self.sim_tick=0
        self.state='playing'
        self.score=0
        self.pos=list(self.world.spawn)
        self.vel=[0.,0.,0.]
        self.facing=[0.,1.]
        self.grounded=True
        self.launch=None
        self.carried=0
        self.successful_lights=0
        self.flames=TUNING['flames']
        self.duration=TUNING['night%d_duration_s'%night]
        self.invuln_ticks=self.dash_cd_ticks=self.pulse_cd_ticks=self.charm_ticks=0
        self.dash_ticks=self.respawn_ticks=0
        self.dash_dir=[0.,1.]
        self.wind={'active':False,'dir_deg':0.}
        self.wind_enabled=True
        self.random_motes=self.random_shades=self.random_drifters=True
        self.previous=dict(DEFAULT_INPUT)
        self.last_pulse=None
        self.events=[]
        self.serials={'M':0,'S':0,'D':0}
        self.reserved={'M':set(),'S':set(),'D':set()}
        self.motes=[]
        self.shades=[]
        self.drifters=[]
        self.charms=[]
        self.lanterns=[dict(id='L'+str(i+1),pos=list(p),lit=False,deposited=0,fuel_units=0,ever_lit=False,relit_count=0) for i,p in enumerate(self.world.lamps)]
        self._scenario({} if scenario is None else scenario)

    @property
    def time_left(self): return self.duration-self.sim_tick/60
    @property
    def capacity(self): return min(TUNING['capacity_max'],TUNING['carry_capacity']+2*self.successful_lights)
    @property
    def required_lights(self): return math.ceil(TUNING['win_ratio']*len(self.lanterns))

    @staticmethod
    def fuel(lamp):
        return float((Decimal(lamp['fuel_units'])/60).quantize(Decimal('.1'),rounding=ROUND_HALF_UP)) if lamp['lit'] else 0

    @staticmethod
    def protected(lamp): return lamp['lit'] and lamp['fuel_units']>=round(TUNING['low_fuel_threshold']*60)

    @staticmethod
    def accepts(lamp): return not lamp['lit'] or lamp['fuel_units']<round(TUNING['fuel_max']*60)

    @staticmethod
    def light_cost(lamp): return TUNING['relight_cost'] if lamp['ever_lit'] else TUNING['lantern_cost']
    @property
    def invuln_until(self): return self.sim_tick+self.invuln_ticks
    @property
    def pulse_ready(self): return self.sim_tick+self.pulse_cd_ticks if self.pulse_cd_ticks else 0

    def _id(self,prefix,identifier=None):
        if identifier is not None:
            if not isinstance(identifier,str) or not identifier: raise ValueError('id must be a nonempty string')
            return identifier
        while True:
            self.serials[prefix]+=1
            name=prefix+str(self.serials[prefix])
            if name not in self.reserved[prefix]:
                self.reserved[prefix].add(name)
                return name

    def _mote(self,pos,kind='random',ttl=0,identifier=None):
        self.motes.append(dict(id=self._id('M',identifier),pos=list(pos),kind=kind,ttl=int(ttl),born=self.sim_tick))

    def _shade(self,pos,identifier=None,state='chase',ticks=0):
        self.shades.append(dict(id=self._id('S',identifier),pos=list(pos),state=state,timer=ticks,
                               push_ticks=0,push_dir=[1.,0.],recoil_dir=[1.,0.],recoil_left=ticks if state=='recoil' else 0,eject=0,target_lantern_id=None))
        return self.shades[-1]

    def _drifter(self,pos,identifier=None,state='idle',stolen=0,ticks=0):
        self.drifters.append(dict(id=self._id('D',identifier),pos=list(pos),state=state,stolen=stolen,
                                 timer=ticks or (240 if state=='flee' else 0)))

    def _scenario(self,data):
        fields(data,['player','random_motes','random_shades','random_drifters','wind_enabled','motes','shades','drifters','charms','lanterns','time_left_s'],'scenario')
        for key in ('random_motes','random_shades','random_drifters','wind_enabled'):
            setattr(self,key,boolean(data.get(key,True),key))
        p=data.get('player',{})
        fields(p,['pos','carried','flames','invuln_ticks','dash_cd_ticks','pulse_cd_ticks','charm_ticks','successful_lights'],'player')
        self.pos=position(p.get('pos',self.pos))
        self.successful_lights=integer(p.get('successful_lights',0),'successful_lights')
        self.carried=integer(p.get('carried',0),'carried',0,self.capacity)
        self.flames=integer(p.get('flames',TUNING['flames']),'flames',0,TUNING['flames'])
        for name in ('invuln_ticks','dash_cd_ticks','pulse_cd_ticks','charm_ticks'):
            setattr(self,name,integer(p.get(name,0),name))
        self.duration=number(data.get('time_left_s',self.duration),'time_left_s',0)
        floor=self.world.floor(self.pos[0],self.pos[2])
        self.grounded=floor is not None and abs(self.pos[1]-floor)<1e-6
        for key in ('motes','shades','drifters','charms','lanterns'):
            if key in data and not isinstance(data[key],list): raise ValueError(key+' must be an array')
        # Reserve explicit IDs before generating defaults, so generated IDs never collide.
        for key,prefix in [('motes','M'),('shades','S'),('drifters','D')]:
            for item in data.get(key,[]):
                if isinstance(item,dict) and 'id' in item:
                    identifier=item['id']
                    if not isinstance(identifier,str) or not identifier or identifier in self.reserved[prefix]: raise ValueError('invalid/duplicate '+key+' id')
                    self.reserved[prefix].add(identifier)
        if 'motes' in data:
            for m in data['motes']:
                if isinstance(m,list): self._mote(position(m)); continue
                fields(m,['id','pos','kind','ttl_s','ttl_ticks'],'mote')
                kind=m.get('kind','random')
                if kind not in ('random','dropped'): raise ValueError('invalid mote kind')
                ttl=integer(m['ttl_ticks'],'ttl_ticks') if 'ttl_ticks' in m else round(number(m.get('ttl_s',8 if kind=='dropped' else 0),'ttl_s',0)*60)
                self._mote(position(m.get('pos')),kind,ttl,m.get('id'))
        elif self.random_motes:
            for p in self.rng.sample(self.world.mote_points,20): self._mote(p)
        for s in data.get('shades',[]):
            fields(s,['id','pos','state','state_ticks_left','target_lantern_id'],'shade')
            state=s.get('state','chase')
            if state not in SHADE_STATES: raise ValueError('invalid shade state')
            entity=self._shade(position(s.get('pos')),s.get('id'),state,integer(s.get('state_ticks_left',0),'state_ticks_left'))
            target=s.get('target_lantern_id')
            if target is not None and target not in [l['id'] for l in self.lanterns]: raise ValueError('unknown target_lantern_id')
            entity['target_lantern_id']=target
        for d in data.get('drifters',[]):
            fields(d,['id','pos','state','stolen','state_ticks_left'],'drifter')
            state=d.get('state','idle')
            if state not in ('idle','chase','flee','removed'): raise ValueError('invalid drifter state')
            self._drifter(position(d.get('pos')),d.get('id'),state,integer(d.get('stolen',0),'stolen',0,3),integer(d.get('state_ticks_left',0),'state_ticks_left'))
        default=[] if self.night==1 else ([dict(id='C1',pos=[35,0,0])] if self.night==2 else [dict(id='C1',pos=[30,0,25]),dict(id='C2',pos=[-30,0,25])])
        seen=set()
        for c in data.get('charms',default):
            fields(c,['id','pos','available','respawn_ticks','respawn_s'],'charm')
            identifier=c.get('id')
            if not isinstance(identifier,str) or not identifier or identifier in seen: raise ValueError('invalid/duplicate charm id')
            seen.add(identifier)
            original=next((e for e in default if e['id']==identifier),None)
            pos=position(c.get('pos',original['pos'] if original else None))
            respawn=integer(c['respawn_ticks'],'respawn_ticks') if 'respawn_ticks' in c else round(number(c.get('respawn_s',0),'respawn_s',0)*60)
            available=boolean(c.get('available',True),'available')
            self.charms.append(dict(id=identifier,pos=pos,available=available,respawn=respawn))
        seen=set()
        for update in data.get('lanterns',[]):
            fields(update,['id','pos','deposited','lit','fuel','ever_lit'],'lantern')
            identifier=update.get('id')
            if not isinstance(identifier,str) or identifier in seen: raise ValueError('invalid/duplicate lantern id')
            lamp=next((l for l in self.lanterns if l['id']==identifier),None)
            if lamp is None: raise ValueError('unknown lantern '+identifier)
            seen.add(identifier)
            if 'pos' in update: lamp['pos']=position(update['pos'])
            deposited=integer(update.get('deposited',0),'deposited',0,10)
            ever=boolean(update.get('ever_lit',False),'ever_lit')
            cost=TUNING['relight_cost'] if ever else TUNING['lantern_cost']
            lit=boolean(update.get('lit',False),'lit') or deposited>=cost
            fuel=number(update.get('fuel',TUNING['fuel_max'] if lit else 0),'fuel',0,TUNING['fuel_max'])
            units=int((Decimal(str(fuel))*60).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) if lit else 0
            lamp.update(lit=lit,deposited=cost if lit else deposited,fuel_units=units,ever_lit=ever or lit)

    def emit(self,name,**data): self.events.append(dict(type='event',tick=self.tick,name=name,data=data))

    def _countdown(self):
        for key in ('invuln_ticks','dash_cd_ticks','pulse_cd_ticks','charm_ticks','dash_ticks'):
            setattr(self,key,max(0,getattr(self,key)-1))
        for s in self.shades: s['timer']=max(0,s['timer']-1)
        for d in self.drifters:
            if d['state']=='flee':
                d['timer']-=1
                if d['timer']<=0: d['state']='removed'
        self.drifters=[d for d in self.drifters if d['state']!='removed']
        for c in self.charms:
            if not c['available']:
                c['respawn']=max(0,c['respawn']-1)
                if c['respawn']==0: c['available']=True
        for m in self.motes:
            if m['kind']=='dropped': m['ttl']-=1
        self.motes=[m for m in self.motes if m['kind']!='dropped' or m['ttl']>0]
        if self.night==3 and self.wind_enabled:
            if self.sim_tick%1800==1680: self.wind['dir_deg']=self.rng.random()*360
            self.wind['active']=self.sim_tick>=1800 and self.sim_tick%1800<300
        self._fuel_step()

    def _fuel_step(self):
        for lamp in self.lanterns:
            if not lamp['lit']: continue
            draining=[s for s in sorted(self.shades,key=id_key) if s['state']=='drain' and s['target_lantern_id']==lamp['id']
                      and lamp['fuel_units']<round(TUNING['low_fuel_threshold']*60) and distance(s['pos'],lamp['pos'])<=2]
            lamp['fuel_units']=max(0,lamp['fuel_units']-round(TUNING['fuel_decay_per_s'])-round(TUNING['drain_per_s'])*len(draining))
            if self.sim_tick%60==0:
                for s in draining: self.emit('fuel_drain',lantern_id=lamp['id'],shade_id=s['id'],fuel=self.fuel(lamp))
        for lamp in self.lanterns:
            if lamp['lit'] and lamp['fuel_units']<=0:
                lamp.update(lit=False,deposited=0,fuel_units=0,ever_lit=True)
                self.emit('lantern_out',lantern_id=lamp['id'])

    def _move(self,c,pressed):
        if self.respawn_ticks:
            self.respawn_ticks-=1
            if not self.respawn_ticks:
                self.pos=list(self.world.spawn); self.vel=[0.,0.,0.]; self.launch=None
                self.grounded=True; self.invuln_ticks=round(TUNING['invuln_s']*60)
            return False
        x,z=c['move']
        d=max(1.,math.hypot(x,z)); x,z=x/d,z/d
        a=math.radians(c['cam_yaw_deg']%360)
        dx,dz=x*math.cos(a)+z*math.sin(a),-x*math.sin(a)+z*math.cos(a)
        if math.hypot(dx,dz)>1e-12:
            length=math.hypot(dx,dz); self.facing=[dx/length,dz/length]
        if pressed['jump'] and self.grounded:
            self.vel[1]=7.; self.grounded=False
        pad=self.world.pad(self.pos) if self.grounded else None
        if pad:
            self.launch=[pad[0],pad[2]]; self.vel[1]=pad[1]; self.grounded=False
        if pressed['dash'] and not self.dash_ticks and (not self.dash_cd_ticks or self.charm_ticks):
            self.dash_ticks=round(TUNING['dash_duration_s']*60)
            self.dash_cd_ticks=0 if self.charm_ticks else round(TUNING['dash_cooldown_s']*60)
            self.dash_dir=direction([0,0,0],[self.launch[0],0,self.launch[1]]) if self.launch else list(self.facing)
            self.emit('dash')
        speed=7.2 if self.charm_ticks else TUNING['player_speed']
        vx,vz=(self.launch if self.launch else [dx*speed,dz*speed])
        if self.dash_ticks: vx,vz=[v*TUNING['dash_speed'] for v in self.dash_dir]
        if self.wind['active']:
            angle=math.radians(self.wind['dir_deg'])
            vx+=2*math.cos(angle); vz+=2*math.sin(angle)
        old=list(self.pos)
        new=[old[0]+vx*DT,old[1],old[2]+vz*DT]
        if self.world.blocked(old,new):
            new[0],new[2]=old[0],old[2]; vx=vz=0.
        floor=self.world.floor(new[0],new[2])
        step_height=max(.11,math.hypot(new[0]-old[0],new[2]-old[2])*.51+.001)
        if self.grounded and floor is not None and abs(old[1]-floor)<=step_height:
            new[1]=floor; self.vel[1]=0.
        else:
            self.grounded=False
            if not self.dash_ticks:
                new[1]+=self.vel[1]*DT-10*DT*DT
                self.vel[1]-=20*DT
                if floor is not None and old[1]>=floor-1e-9 and new[1]<=floor:
                    new[1]=floor; self.vel[1]=0.; self.grounded=True; self.launch=None
        self.pos=new
        self.vel[0],self.vel[2]=vx,vz
        if self.pos[1]<-10:
            lost=self.carried; self.carried=0; self.flames=max(0,self.flames-1)
            self.emit('player_hit',by='fall',flames=self.flames,dropped=0,lost=lost)
            self.respawn_ticks=60 if self.flames else 0
            return False
        return True

    def _pickup(self):
        remaining=[]
        for m in self.motes:
            if self.carried<self.capacity and distance(self.pos,m['pos'])<=TUNING['pickup_radius'] and abs(self.pos[1]-m['pos'][1])<=1.5:
                self.carried+=1; self.emit('mote_picked',carried=self.carried)
            else: remaining.append(m)
        self.motes=remaining
        for c in self.charms:
            if c['available'] and distance(self.pos,c['pos'])<=TUNING['pickup_radius'] and abs(self.pos[1]-c['pos'][1])<=1.5:
                c['available']=False; c['respawn']=2700; self.charm_ticks=600
                self.emit('charm_picked',charm_id=c['id'],charm_ticks=600)

    def _deposit(self):
        candidates=[l for l in self.lanterns if self.accepts(l) and distance(self.pos,l['pos'])<=TUNING['interact_radius']]
        if candidates and self.carried:
            l=min(candidates,key=lambda e:(distance(self.pos,e['pos']),e['id']))
            if l['lit']:
                max_units=round(TUNING['fuel_max']*60); per_mote=round(TUNING['fuel_per_mote']*60)
                amount=min(self.carried,(max_units-l['fuel_units']+per_mote-1)//per_mote)
                if amount:
                    self.carried-=amount; l['fuel_units']=min(max_units,l['fuel_units']+per_mote*amount)
                    self.score+=amount*TUNING['score']['per_mote']
                    self.emit('refuel',lantern_id=l['id'],amount=amount,fuel=self.fuel(l))
                return
            amount=min(self.carried,self.light_cost(l)-l['deposited'])
            self.carried-=amount; l['deposited']+=amount; self.score+=amount*TUNING['score']['per_mote']
            self.emit('deposit',lantern_id=l['id'],amount=amount,deposited=l['deposited'])
            if l['deposited']==self.light_cost(l):
                relight=l['ever_lit']
                l.update(lit=True,fuel_units=round(TUNING['fuel_max']*60),ever_lit=True)
                l['relit_count']+=int(relight); self.successful_lights+=1
                self.score+=TUNING['score']['per_relight'] if relight else TUNING['score']['per_lantern']
                self.emit('lantern_lit',lantern_id=l['id'],relight=relight)

    def _lights(self):
        for s in self.shades:
            inside=any(self.protected(l) and distance(s['pos'],l['pos'])<6-1e-8 for l in self.lanterns)
            if not inside: s['eject']=0
            if inside and not s['eject']: s['eject']=30

    def _pulse(self):
        if self.carried<TUNING['pulse_cost'] or self.pulse_cd_ticks: return
        self.carried-=TUNING['pulse_cost']; self.pulse_cd_ticks=round(TUNING['pulse_cooldown_s']*60)
        self.last_pulse=(self.sim_tick,list(self.pos))
        center=[self.pos[0],self.pos[1]+.8,self.pos[2]]
        def inside(e): return math.dist(center,e['pos'])<=TUNING['pulse_radius']
        stunned=[]
        for s in sorted(self.shades,key=id_key):
            if inside(s):
                reward=TUNING['score']['per_draining_stun'] if s['state']=='drain' else TUNING['score']['per_stun']
                s['state']='stunned'; s['timer']=round(TUNING['pulse_stun_s']*60); s['push_ticks']=15
                s['push_dir']=direction(self.pos,s['pos'])
                self.score+=reward; stunned.append(s['id'])
        self.emit('pulse',stunned_ids=stunned)
        for d in sorted(self.drifters,key=id_key):
            if not inside(d): continue
            if d['state']=='chase': d.update(state='flee',timer=240)
            elif d['state']=='flee' and d['stolen']:
                amount=d['stolen']
                floor=self.world.floor(d['pos'][0],d['pos'][2])
                drop=[d['pos'][0],floor if floor is not None else 0,d['pos'][2]]
                for _ in range(amount): self._mote(drop,'dropped',480)
                d.update(stolen=0,timer=120)
                self.emit('drifter_drop',drifter_id=d['id'],amount=amount)

    def _shade_move(self,s,dx,dz):
        old=s['pos']; candidate=[old[0]+dx,old[1],old[2]+dz]
        floor=self.world.floor(candidate[0],candidate[2])
        old_floor=self.world.floor(old[0],old[2])
        foot=old_floor if old_floor is not None else old[1]
        if floor is None or self.world.blocked([old[0],foot,old[2]],[candidate[0],foot,candidate[2]]): return
        for l in self.lanterns:
            if self.protected(l) and distance(old,l['pos'])>=6-1e-7 and distance(candidate,l['pos'])<6:
                u=direction(l['pos'],candidate)
                candidate[0]=l['pos'][0]+u[0]*6; candidate[2]=l['pos'][2]+u[1]*6
        candidate[1]=old[1]+floor-(old_floor if old_floor is not None else floor)
        s['pos']=candidate

    def _move_shades(self):
        speed=4.5 if self.night==3 else TUNING['shade_speed']
        for s in sorted(self.shades,key=id_key):
            woke=s['state']=='stunned' and s['timer']==0
            if woke: s['state']='wander'; s['target_lantern_id']=None
            if s['state']=='drain':
                target=next((l for l in self.lanterns if l['id']==s['target_lantern_id']),None)
                if target is None or not target['lit'] or self.protected(target) or distance(s['pos'],target['pos'])>2:
                    s['state']='wander'; s['target_lantern_id']=None; woke=True
                elif distance(self.pos,s['pos'])<=6:
                    s['state']='chase'; s['target_lantern_id']=None
                else: continue
            if s['eject']:
                if s['state']=='stunned' and s['push_ticks']:
                    self._shade_move(s,s['push_dir'][0]*TUNING['pulse_push_m']/15,s['push_dir'][1]*TUNING['pulse_push_m']/15)
                    s['push_ticks']-=1
                lamp=next((l for l in self.lanterns if self.protected(l) and distance(s['pos'],l['pos'])<6-1e-8),None)
                if lamp:
                    u=direction(lamp['pos'],s['pos']); amount=(6-distance(s['pos'],lamp['pos']))/s['eject']
                    s['pos'][0]+=u[0]*amount; s['pos'][2]+=u[1]*amount
                s['eject']-=1
                continue
            if s['state']=='spawning' and s['timer']:
                continue
            if s['state']=='stunned' and s['timer']:
                if s['push_ticks']:
                    self._shade_move(s,s['push_dir'][0]*TUNING['pulse_push_m']/15,s['push_dir'][1]*TUNING['pulse_push_m']/15)
                    s['push_ticks']-=1
                continue
            if s['state']=='recoil' and s['recoil_left']:
                self._shade_move(s,s['recoil_dir'][0]*2/60,s['recoil_dir'][1]*2/60)
                s['recoil_left']-=1
                if not s['recoil_left']:
                    s['state']='chase' if distance(self.pos,s['pos'])<=12 else 'wander'
                continue
            d=distance(self.pos,s['pos'])
            chase=not woke and ((s['state']=='chase' and d<=18) or d<=12)
            s['state']='chase' if chase else 'wander'
            if chase:
                if d>1e-12:
                    u=direction(s['pos'],self.pos); amount=min(d,speed*DT)
                    self._shade_move(s,u[0]*amount,u[1]*amount)
            else:
                self._wander(s,speed)

    def _wander(self,s,speed):
        """Same wander motion for gameplay and the benchmark's forced-wander population."""
        weak=[l for l in self.lanterns if l['lit'] and not self.protected(l)]
        targets=weak or [l for l in self.lanterns if not l['lit']]
        if targets:
            target=min(targets,key=lambda l:(distance(s['pos'],l['pos']),l['id']))
            dest=target['pos']; remaining=distance(s['pos'],dest)
            amount=min(remaining,speed*DT); u=direction(s['pos'],dest)
            if amount: self._shade_move(s,u[0]*amount,u[1]*amount)
            if target['lit'] and distance(s['pos'],dest)<=2:
                s['state']='drain'; s['target_lantern_id']=target['id']

    def _move_drifters(self):
        for d in self.drifters:
            if d['state']=='flee':
                u=direction(self.pos,d['pos']); speed=7
            else:
                chase=self.carried>=5 and distance(self.pos,d['pos'])<=15
                d['state']='chase' if chase else 'idle'
                if chase: u=direction(d['pos'],self.pos); speed=7
                else:
                    phase=(sum(map(ord,d['id']))*.13+self.sim_tick/120)
                    u=[math.cos(phase),math.sin(phase)]; speed=2
            d['pos'][0]+=u[0]*speed*DT; d['pos'][2]+=u[1]*speed*DT

    def _contact(self):
        for d in sorted(self.drifters,key=id_key):
            if d['state'] in ('idle','chase') and self.carried>0 and distance(self.pos,d['pos'])<=1.2:
                amount=min(3,self.carried); self.carried-=amount
                d.update(stolen=amount,state='flee',timer=240)
                self.emit('drifter_steal',drifter_id=d['id'],amount=amount,carried=self.carried)
        if self.invuln_ticks: return
        for s in sorted(self.shades,key=id_key):
            if s['state'] not in ('wander','chase') or s['eject']: continue
            if distance(self.pos,s['pos'])<=TUNING['shade_hit_radius'] and abs(self.pos[1]-s['pos'][1])<=1.5:
                self.flames=max(0,self.flames-1); self.invuln_ticks=round(TUNING['invuln_s']*60)
                dropped=math.floor(self.carried*TUNING['hit_drop_ratio']); self.carried-=dropped
                for _ in range(dropped):
                    a=self.rng.random()*math.tau; radius=self.rng.uniform(1.5,2.5)
                    x,z=self.pos[0]+radius*math.cos(a),self.pos[2]+radius*math.sin(a)
                    floor=self.world.floor(x,z)
                    self._mote([x,self.pos[1] if floor is None else floor,z],'dropped',480)
                s.update(state='recoil',timer=60,recoil_left=60,recoil_dir=direction(self.pos,s['pos']))
                self.emit('player_hit',by='shade',flames=self.flames,dropped=dropped)
                break

    def _spawn(self):
        if self.random_motes and self.sim_tick%240==0 and len(self.motes)<30:
            free=[p for p in self.world.mote_points if not any(distance(p,m['pos'])<1e-6 and abs(p[1]-m['pos'][1])<1e-6 for m in self.motes)]
            if free: self._mote(self.rng.choice(free))
        interval={1:480,2:420,3:360}[self.night]
        if self.random_shades and self.sim_tick>=300 and (self.sim_tick-300)%interval==0:
            for _ in range(2 if self.sim_tick==300 else 1):
                if len(self.shades)>={1:6,2:8,3:10}[self.night]: break
                candidates=[p for p in self.world.fog_points if distance(p,self.pos)>=15 and not any(distance(p,s['pos'])<1 for s in self.shades)]
                if candidates:
                    p=list(self.rng.choice(candidates)); p[1]+=.8
                    s=self._shade(p,state='spawning',ticks=30)
                    self.emit('shade_spawned',id=s['id'])
        if self.night>1 and self.random_drifters and self.sim_tick%1200==0 and len(self.drifters)<2:
            p=list(self.rng.choice(self.world.fog_points)); p[1]+=.8
            self._drifter(p)

    def _finish(self,state,reason):
        self.state=state
        if state=='won':
            self.score+=sum(TUNING['score']['per_dawn_lantern']+l['fuel_units']//60 for l in self.lanterns if l['lit'])
            self.score+=TUNING['score']['per_flame_left']*self.flames
        self.emit('game_over',result=state,reason=reason)

    def step(self,controls=None):
        if self.state in ('won','lost'): return []
        c=dict(DEFAULT_INPUT,**(controls or {}))
        self.tick+=1; self.events=[]
        pressed={k:c[k] and not self.previous.get(k,False) for k in ('jump','dash','pulse','interact','pause')}
        self.previous=dict(c)
        if pressed['pause']:
            self.state='playing' if self.state=='paused' else 'paused'
            self.emit('resumed' if self.state=='playing' else 'paused')
        if self.state=='paused': return self.events
        self.sim_tick+=1
        if self.sim_tick==1: self.emit('night_start',night=self.night)
        self._countdown()
        active=self._move(c,pressed)
        if active:
            self._pickup()
            if pressed['interact']: self._deposit()
        self._lights()
        if active and pressed['pulse']: self._pulse()
        self._move_shades(); self._move_drifters()
        if active: self._contact()
        self._spawn()
        if self.flames<=0: self._finish('lost','no_flames')
        elif self.time_left<=0:
            won=sum(l['lit'] for l in self.lanterns)>=self.required_lights
            self._finish('won' if won else 'lost','dawn_survived' if won else 'dawn')
        return self.events

    def snapshot(self):
        return dict(type='snapshot',tick=self.tick,sim_tick=self.sim_tick,night=self.night,state=self.state,
                    time_left_s=self.time_left,score=self.score,wind=dict(self.wind),
                    player=dict(pos=rounded(self.pos),vel=rounded([self.vel[0],0 if self.dash_ticks else self.vel[1],self.vel[2]]),
                                flames=self.flames,carried=self.carried,capacity=self.capacity,grounded=self.grounded,invuln=self.invuln_ticks>0,
                                dash_cd_s=self.dash_cd_ticks/60,pulse_cd_s=self.pulse_cd_ticks/60,charm_s=self.charm_ticks/60),
                    lanterns=[dict(id=l['id'],pos=rounded(l['pos']),lit=l['lit'],deposited=l['deposited'],fuel=self.fuel(l),ever_lit=l['ever_lit'],relit_count=l['relit_count']) for l in self.lanterns],
                    shades=[dict(id=s['id'],pos=rounded(s['pos']),state=s['state']) for s in sorted(self.shades,key=id_key)],
                    motes_active=len(self.motes),motes=[dict(id=m['id'],pos=rounded(m['pos']),kind=m['kind'],ttl_s=m['ttl']/60) for m in self.motes],
                    drifters=[dict(id=d['id'],pos=rounded(d['pos']),state=d['state'],stolen=d['stolen']) for d in sorted(self.drifters,key=id_key)],
                    charms=[dict(id=c['id'],available=c['available'],respawn_s=c['respawn']/60) for c in self.charms])
