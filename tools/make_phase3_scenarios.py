"""Versioned v1.2 input fixtures; never edits captured engine output."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    target=ROOT/'tests/scenarios/v12'; target.mkdir(parents=True,exist_ok=True)
    def quiet(**kw): return dict(random_motes=False,random_shades=False,random_drifters=False,wind_enabled=False,**kw)
    cases={
        'fuel-out':(1,quiet(lanterns=[{'id':'L1','lit':True,'fuel':1}]),[],65,'lantern_out'),
        'refuel':(1,quiet(player={'carried':5},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':90}]),[{'tick':0,'interact':True}],1,'refuel'),
        'relight':(1,quiet(player={'carried':5},lanterns=[{'id':'L1','pos':[0,0,0],'ever_lit':True}]),[{'tick':0,'interact':True}],1,'lantern_lit'),
        'capacity':(1,quiet(player={'carried':10},lanterns=[{'id':'L1','pos':[0,0,0]}]),[{'tick':0,'interact':True}],1,'lantern_lit'),
        'drain-stack':(1,quiet(player={'pos':[30,0,0]},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],shades=[{'id':s,'pos':[0,.8,0],'state':'drain','target_lantern_id':'L1'} for s in ('S1','S2')]),[],60,'fuel_drain'),
        'drain-pause':(1,quiet(player={'pos':[30,0,0]},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],shades=[{'id':'S1','pos':[0,.8,0],'state':'drain','target_lantern_id':'L1'}]),[{'tick':0,'pause':True},{'tick':1,'pause':False},{'tick':60,'pause':True},{'tick':61,'pause':False}],121,'fuel_drain'),
        'drain-pulse':(1,quiet(player={'carried':3},lanterns=[{'id':'L1','pos':[3,0,0],'lit':True,'fuel':20}],shades=[{'id':'S1','pos':[3,.8,0],'state':'drain','target_lantern_id':'L1'}]),[{'tick':0,'pulse':True}],1,'pulse'),
        'refuel-eject':(1,quiet(player={'carried':2},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],shades=[{'id':'S1','pos':[1,.8,0],'state':'drain','target_lantern_id':'L1'}]),[{'tick':0,'interact':True}],30,'refuel'),
        'all-lit-running':(1,quiet(lanterns=[{'id':'L'+str(i),'lit':True} for i in range(1,6)]),[],60,'night_start')
    }
    for n,needed in ((1,3),(2,4),(3,5)):
        for count,kind in ((needed,'won'),(needed-1,'lost')):
            lamps=[{'id':'L'+str(i),'lit':True} for i in range(1,count+1)]
            cases['dawn-%s-night%d'%(kind,n)]=(n,quiet(lanterns=lamps,time_left_s=1/60),[],1,'game_over')
    lamps=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':1/60},{'id':'L2','lit':True},{'id':'L3','lit':True}]
    cases['dawn-expiry']=(1,quiet(lanterns=lamps,time_left_s=1/60),[],1,'game_over')
    cases['dawn-relight']=(1,quiet(player={'carried':5},lanterns=lamps,time_left_s=1/60),[{'tick':0,'interact':True}],1,'game_over')
    index=[]
    for name,(night,scenario,frames,ticks,event) in cases.items():
        (target/(name+'.json')).write_text(json.dumps(scenario,indent=2)+'\n',encoding='utf-8')
        (target/(name+'.inputs.json')).write_text(json.dumps({'frames':frames},indent=2)+'\n',encoding='utf-8')
        index.append(dict(name=name,night=night,ticks=ticks,event=event))
    challenge=quiet(player={'carried':10},lanterns=[{'id':'L1','pos':[-5,0,0],'lit':True,'fuel':30},{'id':'L2','pos':[0,0,5],'lit':True,'fuel':30},{'id':'L3','pos':[5,0,0],'lit':True,'fuel':30}],motes=[[-4,0,0]]*15+[[4,0,0]]*15,time_left_s=120)
    (target/'maintenance.json').write_text(json.dumps(challenge,indent=2)+'\n',encoding='utf-8')
    (target/'index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print('Generated %d v1.2 scenario/input pairs and maintenance challenge.'%len(index))


if __name__=='__main__': main()
