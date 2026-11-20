"""Generate versioned test INPUT fixtures, never fabricated engine output."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    target=ROOT/'tests/scenarios/v11'; target.mkdir(parents=True,exist_ok=True)
    def quiet(**data): return dict(random_motes=False,random_shades=False,random_drifters=False,wind_enabled=False,**data)
    cases={
        'deposit':(1,quiet(player={'carried':10},lanterns=[{'id':'L1','pos':[0,0,0]}]),[{'tick':0,'interact':True}],10,'lantern_lit'),
        'dash':(1,quiet(),[{'tick':0,'move':[0,1],'dash':True},{'tick':1,'dash':False}],20,'dash'),
        'fall':(1,quiet(player={'pos':[41,-10,0],'carried':6,'invuln_ticks':1000}),[],65,'player_hit'),
        'pause':(1,quiet(player={'charm_ticks':100},motes=[{'pos':[8,0,0],'kind':'dropped','ttl_ticks':80}]),[{'tick':0,'move':[0,1]},{'tick':10,'pause':True},{'tick':11,'pause':False},{'tick':70,'pause':True},{'tick':71,'pause':False}],100,'resumed'),
        'pulse':(1,quiet(player={'carried':6},shades=[{'id':'S1','pos':[4,.8,0]}]),[{'tick':0,'pulse':True},{'tick':1,'pulse':False}],150,'pulse'),
        'drifter-steal':(2,quiet(player={'carried':9},drifters=[{'id':'D1','pos':[0,.8,0],'state':'chase'}],shades=[{'pos':[0,.8,0]}]),[],3,'drifter_steal'),
        'drifter-drop':(2,quiet(player={'carried':3},drifters=[{'id':'D1','pos':[3,.8,0],'state':'flee','stolen':3}]),[{'tick':0,'pulse':True},{'tick':1,'pulse':False}],130,'drifter_drop'),
        'charm':(2,quiet(player={'pos':[35,0,0]}),[{'tick':1,'move':[1,0],'dash':True},{'tick':2,'dash':False},{'tick':14,'dash':True}],30,'charm_picked'),
        'launch':(2,quiet(player={'pos':[20,0,18]}),[{'tick':0,'move':[-1,0]}],85,'night_start'),
        'tiers':(3,quiet(player={'pos':[0,3,13]}),[],55,'night_start'),
        'wind':(3,dict(quiet(),wind_enabled=True),[],2101,'night_start')
    }
    for n in (1,2,3):
        lamps=[{'id':'L'+str(i),'lit':True} for i in range(1,{1:5,2:6,3:7}[n]+1)]
        cases['win-night%d'%n]=(n,quiet(lanterns=lamps),[],10,'game_over')
    index=[]
    for name,(night,scenario,frames,ticks,event) in cases.items():
        (target/(name+'.json')).write_text(json.dumps(scenario,indent=2)+'\n',encoding='utf-8')
        (target/(name+'.inputs.json')).write_text(json.dumps({'frames':frames},indent=2)+'\n',encoding='utf-8')
        index.append(dict(name=name,night=night,ticks=ticks,event=event))
    for n in (1,2,3):
        (target/('benchmark%d.json'%n)).write_text(json.dumps(dict(player={'invuln_ticks':100000},wind_enabled=False))+'\n',encoding='utf-8')
    (target/'index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print('Generated %d v1.1 scenario/input pairs.'%len(index))


if __name__=='__main__': main()
