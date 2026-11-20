"""Retained regression behaviors, with replaced expectations migrated to v1.2."""
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from game import load_json,run_headless
from src.lantern_island.model import Game,TUNING,DEFAULT_INPUT,distance,validate_inputs
from src.lantern_island.maps import World,PALETTE

ROOT=Path(__file__).resolve().parents[1]


def quiet(**data): return dict(random_motes=False,random_shades=False,random_drifters=False,wind_enabled=False,**data)
def controls(**data): return dict(DEFAULT_INPUT,**data)
def advance(game,n,c=None):
    events=[]
    for _ in range(n): events.extend(game.step(c))
    return events
def named(events,name): return [e for e in events if e['name']==name]
def replay(game,ticks=60,frames=None,every=10):
    out=io.StringIO(); run_headless(game,frames or [],ticks,every,out)
    return [json.loads(l) for l in out.getvalue().splitlines()]


class ContractTests(unittest.TestCase):
    def test_manifest_standard_numbers(self):
        m=json.loads((ROOT/'game.contract.json').read_text(encoding='utf-8'))
        self.assertEqual(m['contract_version'],'1.2')
        expected=dict(player_speed=6,carry_capacity=10,lantern_cost=10,pickup_radius=1,interact_radius=2,
                      pulse_cost=3,pulse_radius=5,pulse_cooldown_s=3,pulse_stun_s=2,pulse_push_m=4,
                      safe_radius=6,shade_speed=4,shade_hit_radius=1,invuln_s=1.5,hit_drop_ratio=.5,
                      dash_speed=14,dash_duration_s=.2,dash_cooldown_s=1.5,night1_duration_s=240,
                      night2_duration_s=270,night3_duration_s=300,fall_enabled=True)
        for k,v in expected.items(): self.assertEqual(TUNING[k],v,k)

    def test_zero_ticks_is_setup_only(self):
        r=replay(Game(scenario=quiet()),0)
        self.assertEqual([e['type'] for e in r],['snapshot','end'])
        self.assertEqual(r[0]['player']['pos'],[0,0,0])
        self.assertEqual(r[0]['score'],0)

    def test_cadence_and_exact_tick_count(self):
        r=replay(Game(scenario=quiet()),123)
        self.assertEqual([e['tick'] for e in r if e['type']=='snapshot'],list(range(0,121,10)))
        self.assertEqual(r[-1]['ticks'],123)
        self.assertEqual(r[-2]['time_left_s'],238)

    def test_movement_speed_and_partial_input_magnitude(self):
        for move,expected in [([0,1],6),([0,.5],3),([1,1],6)]:
            g=Game(scenario=quiet()); advance(g,60,controls(move=move))
            self.assertAlmostEqual(distance(g.pos,[0,0,0]),expected)

    def test_yaw_formula(self):
        g=Game(scenario=quiet()); advance(g,60,controls(move=[0,1],cam_yaw_deg=90))
        self.assertAlmostEqual(g.pos[0],6); self.assertAlmostEqual(g.pos[2],0)

    def test_partial_frame_persistence(self):
        g=Game(scenario=quiet())
        replay(g,30,[{'tick':0,'move':[0,1]},{'tick':10,'cam_yaw_deg':90},{'tick':20,'move':[0,0]}])
        self.assertAlmostEqual(g.pos[0],1); self.assertAlmostEqual(g.pos[2],1)

    def test_jump_ballistic_and_no_held_repeat(self):
        g=Game(scenario=quiet()); g.step(controls(jump=True))
        self.assertAlmostEqual(g.pos[1],7/60-10/3600)
        advance(g,120,controls(jump=True)); self.assertTrue(g.grounded)
        self.assertEqual(g.pos[1],0)
        g.step(); g.step(controls(jump=True)); self.assertGreater(g.pos[1],0)

    def test_pickup_inclusive_radius_height_capacity_no_score(self):
        g=Game(scenario=quiet(motes=[[1,1.5,0]]*12+[[0,1.501,0]]))
        e=g.step(); self.assertEqual(g.carried,10); self.assertEqual(len(g.motes),3)
        self.assertEqual(g.score,0); self.assertEqual(len(named(e,'mote_picked')),10)

    def test_pickup_outside_radius(self):
        g=Game(scenario=quiet(motes=[[1.001,0,0],[0,1.501,0]])); g.step()
        self.assertEqual(g.carried,0)

    def test_partial_deposit_edge_and_scoring(self):
        g=Game(scenario=quiet(player={'carried':4},lanterns=[{'id':'L1','pos':[2,0,0]}]))
        e=g.step(controls(interact=True)); self.assertEqual(named(e,'deposit')[0]['data']['amount'],4)
        self.assertEqual(g.score,20); g.carried=6
        self.assertFalse(named(g.step(controls(interact=True)),'deposit'))
        g.step(); g.step(controls(interact=True))
        self.assertTrue(g.lanterns[0]['lit']); self.assertEqual(g.score,150)

    def test_nearest_tie_id_and_only_remaining(self):
        g=Game(scenario=quiet(player={'carried':10},lanterns=[{'id':'L2','pos':[1,0,0]},{'id':'L1','pos':[-1,0,0],'deposited':8}]))
        g.step(controls(interact=True)); self.assertEqual(g.carried,8)
        self.assertTrue(g.lanterns[0]['lit']); self.assertEqual(g.lanterns[1]['deposited'],0)

    def test_far_or_empty_deposit(self):
        for scenario in (quiet(player={'carried':10}),quiet(lanterns=[{'id':'L1','pos':[0,0,0]}])):
            self.assertFalse(named(Game(scenario=scenario).step(controls(interact=True)),'deposit'))

    def test_scenario_updates_without_events_or_score(self):
        g=Game(scenario=quiet(lanterns=[{'id':'L3','pos':[2,0,3],'lit':True}]))
        self.assertEqual(g.lanterns[2]['pos'],[2,0,3]); self.assertEqual(g.events,[])
        self.assertEqual(g.score,0); self.assertEqual(len(g.lanterns),5)

    def test_explicit_empty_lists_and_flags(self):
        g=Game(scenario={'motes':[],'shades':[],'drifters':[],'charms':[]})
        self.assertEqual(len(g.motes)+len(g.shades)+len(g.drifters)+len(g.charms),0)
        g=Game(scenario=quiet(),night=2); advance(g,1300)
        self.assertEqual(len(g.shades)+len(g.motes)+len(g.drifters),0)

    def test_pulse_is_3d_and_locks_targets(self):
        g=Game(scenario=quiet(player={'carried':6},shades=[{'id':'edge','pos':[5,.8,0]},{'id':'high','pos':[0,6,0]}]))
        e=g.step(controls(pulse=True))
        self.assertEqual(named(e,'pulse')[0]['data']['stunned_ids'],['edge'])
        self.assertEqual(g.carried,3); self.assertEqual(g.score,5)
        self.assertEqual(g.shades[0]['state'],'stunned')
        advance(g,14); self.assertAlmostEqual(g.shades[0]['pos'][0],9)

    def test_stun_duration_and_push_refresh(self):
        g=Game(scenario=quiet(player={'carried':6},shades=[{'pos':[0,.8,0]}]))
        g.step(controls(pulse=True)); advance(g,119)
        self.assertEqual(g.shades[0]['state'],'stunned'); g.step()
        self.assertNotEqual(g.shades[0]['state'],'stunned')

    def test_pulse_cost_cooldown_and_rising_edge(self):
        g=Game(scenario=quiet(player={'carried':10}))
        g.step(controls(pulse=True)); advance(g,179,controls(pulse=True))
        self.assertEqual(g.carried,7); g.step(controls(pulse=True)); self.assertEqual(g.carried,7)
        g.step(); g.step(controls(pulse=True)); self.assertEqual(g.carried,4)
        poor=Game(scenario=quiet(player={'carried':2})); self.assertFalse(named(poor.step(controls(pulse=True)),'pulse'))

    def test_dash_distance_duration_and_cooldown(self):
        g=Game(scenario=quiet()); g.step(controls(dash=True)); advance(g,11)
        self.assertAlmostEqual(g.pos[2],2.8)
        before=g.pos[2]; g.step(); self.assertEqual(g.pos[2],before)
        self.assertGreater(g.dash_cd_ticks,0)
        self.assertFalse(named(g.step(controls(dash=True)),'dash'))

    def test_dash_uses_facing_and_air_locks_height(self):
        g=Game(scenario=quiet()); g.step(controls(move=[1,0])); g.step(controls(jump=True))
        y=g.pos[1]; x=g.pos[0]; g.step(controls(dash=True)); advance(g,11)
        self.assertEqual(g.pos[1],y); self.assertAlmostEqual(g.pos[0]-x,2.8)

    def test_hit_half_drop_invulnerability_recoil_and_single_hit(self):
        g=Game(scenario=quiet(player={'carried':9},shades=[{'id':'S2','pos':[0,.8,0]},{'id':'S1','pos':[0,.8,0]}]))
        e=g.step(); hits=named(e,'player_hit')
        self.assertEqual(len(hits),1); self.assertEqual(hits[0]['data'],dict(by='shade',flames=2,dropped=4))
        self.assertEqual(g.invuln_ticks,90); self.assertEqual(g.carried,5)
        self.assertEqual(next(s for s in g.shades if s['id']=='S1')['state'],'recoil')
        self.assertEqual(len(g.motes),4)
        self.assertTrue(all(1.5<=distance(m['pos'],g.pos)<=2.5 for m in g.motes))
        self.assertTrue(all(m['kind']=='dropped' and m['ttl']==480 for m in g.motes))

    def test_hit_height_gate(self):
        g=Game(scenario=quiet(shades=[{'pos':[0,3,0],'state':'stunned','state_ticks_left':100}]))
        g.step(); self.assertEqual(g.flames,3)

    def test_fall_ignores_invulnerability_and_respawns_after_60(self):
        g=Game(scenario=quiet(player={'pos':[41,-10,0],'carried':7,'invuln_ticks':500}))
        e=g.step(); self.assertEqual(named(e,'player_hit')[0]['data'],dict(by='fall',flames=2,dropped=0,lost=7))
        advance(g,59); self.assertLess(g.pos[1],-10)
        g.step(); self.assertEqual(g.pos,[0,0,0]); self.assertEqual(g.invuln_ticks,90)
        self.assertEqual(g.vel,[0,0,0]); self.assertEqual(g.flames,2)

    def test_no_flames_priority_over_all_lit_and_dawn(self):
        lamps=[{'id':'L'+str(i),'lit':True} for i in range(1,6)]
        g=Game(scenario=quiet(player={'flames':0},lanterns=lamps,time_left_s=0))
        g.step(); self.assertEqual(g.state,'lost'); self.assertEqual(g.events[-1]['data']['reason'],'no_flames')

    def test_win_at_dawn_and_bonus(self):
        lamps=[{'id':'L'+str(i),'lit':True} for i in range(1,5)]+[{'id':'L5','pos':[0,0,0],'deposited':9}]
        g=Game(scenario=quiet(player={'carried':1},lanterns=lamps,time_left_s=1/60))
        r=replay(g,100,[{'tick':0,'interact':True}])
        self.assertEqual(r[-1],dict(type='end',ticks=1,state='won',score=1001))

    def test_dawn_exact_step(self):
        g=Game(scenario=quiet(time_left_s=1)); r=replay(g,1000)
        self.assertEqual(r[-1]['ticks'],60); self.assertEqual(g.state,'lost')
        self.assertEqual(g.events[-1]['data']['reason'],'dawn')

    def test_pause_freezes_every_counter_and_simulation(self):
        g=Game(scenario=quiet(player={'carried':5,'invuln_ticks':50,'dash_cd_ticks':30,'pulse_cd_ticks':40,'charm_ticks':60},motes=[{'pos':[8,0,0],'kind':'dropped','ttl_ticks':5}],shades=[{'pos':[10,.8,0],'state':'stunned','state_ticks_left':90}]))
        before=g.snapshot(); g.step(controls(pause=True)); advance(g,100,controls(pause=True,move=[1,0]))
        after=g.snapshot(); self.assertEqual(after['state'],'paused'); self.assertEqual(after['tick'],101)
        for key in ('sim_tick','time_left_s','player','shades','motes','charms'): self.assertEqual(after[key],before[key],key)
        g.step(); g.step(controls(pause=True)); self.assertEqual(g.sim_tick,1)

    def test_pause_runner_does_not_treat_pause_as_terminal(self):
        r=replay(Game(scenario=quiet()),6,[{'tick':0,'pause':True},{'tick':1,'pause':False},{'tick':4,'pause':True}],1)
        self.assertEqual(r[-1]['ticks'],6); self.assertEqual(r[-2]['sim_tick'],2)
        self.assertIn('resumed',[e.get('name') for e in r])

    def test_safe_zone_ejects_without_damage_in_30_steps(self):
        g=Game(scenario=quiet(lanterns=[{'id':'L1','pos':[0,0,0],'lit':True}],shades=[{'pos':[0,.8,0]}]))
        self.assertEqual(g.snapshot()['shades'][0]['pos'],[0,.8,0])
        advance(g,30); self.assertGreaterEqual(distance(g.shades[0]['pos'],[0,0,0]),6-1e-6)
        self.assertEqual(g.flames,3)

    def test_safe_boundary_blocks_chase(self):
        g=Game(scenario=quiet(lanterns=[{'id':'L1','pos':[0,0,0],'lit':True}],shades=[{'pos':[10,.8,0]}]))
        advance(g,200); self.assertGreaterEqual(distance(g.shades[0]['pos'],[0,0,0]),6-1e-6)

    def test_chase_detection_hysteresis_and_speed(self):
        g=Game(scenario=quiet(shades=[{'pos':[10,.8,0]}])); advance(g,60)
        self.assertAlmostEqual(g.shades[0]['pos'][0],6)
        g.pos=[-20,0,0]; g.step(); self.assertEqual(g.shades[0]['state'],'wander')

    def test_mote_initial_counts_points_and_spawn_schedule(self):
        for n in (1,2,3):
            g=Game(night=n)
            self.assertEqual(len(g.motes),20); self.assertEqual(len({tuple(m['pos']) for m in g.motes}),20)
            self.assertTrue(all(m['pos'] in g.world.mote_points for m in g.motes))
        g=Game(scenario={'motes':[],'random_shades':False,'random_drifters':False})
        advance(g,239); self.assertEqual(len(g.motes),0)
        g.step(); self.assertEqual(len(g.motes),1)

    def test_shade_schedule_cap_and_distance(self):
        g=Game(scenario={'random_motes':False})
        advance(g,299); self.assertEqual(len(g.shades),0)
        e=g.step(); self.assertEqual(len(named(e,'shade_spawned')),2)
        self.assertTrue(all(s['state']=='spawning' and distance(s['pos'],g.pos)>=15 for s in g.shades))

    def test_id_reservation_and_seed_determinism(self):
        g=Game(scenario=quiet(shades=[{'pos':[10,0,0]},{'id':'S1','pos':[15,0,0]}]))
        self.assertEqual(len({s['id'] for s in g.shades}),2)
        a=replay(Game(12,quiet()),100); b=replay(Game(12,quiet()),100)
        self.assertEqual(a,b); self.assertNotEqual(Game(12).snapshot(),Game(13).snapshot())

    def test_snapshot_v11_fields_and_rounding(self):
        s=Game(scenario=quiet(player={'pos':[.123456,0,-.987654]})).snapshot()
        self.assertEqual(s['player']['pos'],[.123,0,-.988])
        self.assertTrue({'vel','grounded','invuln','dash_cd_s','pulse_cd_s','charm_s'}<=s['player'].keys())
        self.assertTrue({'night','wind','motes','drifters','charms'}<=s.keys())

    def test_invalid_inputs(self):
        for data in ({},{'frames':None},{'frames':[{'tick':0},{'tick':0}]},{'frames':[{'tick':-1}]},
                     {'frames':[{'tick':True}]},{'frames':[{'tick':0,'pause':1}]},
                     {'frames':[{'tick':0,'move':[2,0]}]},{'frames':[{'tick':0,'move':[0]}]},
                     {'frames':[{'tick':0,'cam_yaw_deg':float('nan')}]},{'frames':[{'tick':0,'oops':1}]}):
            with self.subTest(data=data),self.assertRaises(ValueError): validate_inputs(data)

    def test_invalid_scenarios(self):
        for data in ([],{'player':None},{'player':{'pos':[0,0]}},{'motes':None},{'random_motes':0},
                     {'player':{'carried':11}},{'time_left_s':-1},{'lanterns':[{'id':'L9'}]},
                     {'shades':[{'pos':[0,0,0],'state':'invalid'}]},{'drifters':[{'pos':[0,0,0],'stolen':4}]}):
            with self.subTest(data=data),self.assertRaises(ValueError): Game(scenario=data)

    def test_cli_all_nights_and_malformed_exit_two(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'out.jsonl'; bad=Path(temp)/'bad.json'; bad.write_text('{"frames":false}',encoding='utf-8')
            for n in (1,2,3):
                cmd=[sys.executable,str(ROOT/'game.py'),'--headless','--night',str(n),'--seed','12','--ticks','2','--out',str(out)]
                p=subprocess.run(cmd,capture_output=True,text=True); self.assertEqual(p.returncode,0,p.stderr)
                self.assertEqual(json.loads(out.read_text().splitlines()[0])['night'],n)
                p=subprocess.run(cmd+['--inputs',str(bad)],capture_output=True,text=True); self.assertEqual(p.returncode,2)
                self.assertTrue(p.stderr)

    def test_bad_json_duplicate_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.json'
            for text in ('{"frames":[],"frames":[]}','{"time_left_s":NaN}'):
                p.write_text(text,encoding='utf-8')
                with self.assertRaises(ValueError): load_json(p)


class NewFeaturesTests(unittest.TestCase):
    def test_drifter_steals_before_hit_ignores_safe_and_invuln(self):
        g=Game(scenario=quiet(player={'carried':9},drifters=[{'id':'D1','pos':[0,.8,0],'state':'chase'}],shades=[{'pos':[0,.8,0]}]),night=2)
        e=g.step(); self.assertEqual([x['name'] for x in e if x['name'] in ('drifter_steal','player_hit')],['drifter_steal','player_hit'])
        self.assertEqual(named(e,'player_hit')[0]['data']['dropped'],3)
        self.assertEqual(g.carried,3); self.assertEqual(g.drifters[0]['stolen'],3)
        safe=Game(scenario=quiet(player={'carried':6,'invuln_ticks':60},drifters=[{'pos':[0,.8,0]}],lanterns=[{'id':'L1','pos':[0,0,0],'lit':True}]),night=2)
        self.assertTrue(named(safe.step(),'drifter_steal')); self.assertEqual(safe.flames,3)

    def test_drifter_chase_condition_and_removal(self):
        g=Game(scenario=quiet(player={'carried':4},drifters=[{'pos':[5,.8,0],'state':'chase'}]),night=2)
        g.step(); self.assertEqual(g.drifters[0]['state'],'idle')
        g.carried=5; g.step(); self.assertEqual(g.drifters[0]['state'],'chase')
        g.pos=list(g.drifters[0]['pos']); e=g.step(); self.assertTrue(named(e,'drifter_steal'))
        advance(g,240); self.assertFalse(g.drifters)

    def test_drifter_contact_cannot_underflow_small_inventory(self):
        g=Game(scenario=quiet(player={'carried':2},drifters=[{'pos':[0,.8,0]}]),night=2)
        e=g.step(); self.assertEqual(named(e,'drifter_steal')[0]['data']['amount'],2)
        self.assertEqual(g.carried,0)

    def test_drifter_pulse_chase_then_flee_drop(self):
        g=Game(scenario=quiet(player={'carried':6},drifters=[{'id':'D1','pos':[3,.8,0],'state':'chase'}]),night=2)
        g.step(controls(pulse=True)); self.assertEqual(g.drifters[0]['state'],'flee'); self.assertEqual(g.drifters[0]['stolen'],0)
        g=Game(scenario=quiet(player={'carried':3},drifters=[{'id':'D1','pos':[3,.8,0],'state':'flee','stolen':3}]),night=2)
        e=g.step(controls(pulse=True)); self.assertEqual(named(e,'drifter_drop')[0]['data']['amount'],3)
        self.assertEqual(len(g.motes),3); self.assertEqual(g.drifters[0]['timer'],120)
        advance(g,120); self.assertFalse(g.drifters)

    def test_drifter_spawn_at_1200_and_cap(self):
        g=Game(scenario={'random_motes':False,'random_shades':False,'wind_enabled':False},night=2)
        advance(g,1199); self.assertEqual(len(g.drifters),0)
        g.step(); self.assertEqual(g.drifters[0]['id'],'D1')
        advance(g,1200); self.assertEqual(len(g.drifters),2)
        advance(g,1200); self.assertEqual(len(g.drifters),2)

    def test_charm_pick_refresh_speed_and_no_dash_cd(self):
        g=Game(scenario=quiet(player={'pos':[35,0,0]}),night=2)
        e=g.step(); self.assertEqual(named(e,'charm_picked')[0]['data']['charm_ticks'],600)
        self.assertEqual(g.charms[0]['respawn'],2700)
        x=g.pos[0]; advance(g,60,controls(move=[1,0])); self.assertAlmostEqual(g.pos[0]-x,7.2)
        g.step(controls(dash=True)); self.assertEqual(g.dash_cd_ticks,0)
        g.step(); self.assertFalse(named(g.step(controls(dash=True)),'dash'))
        advance(g,12); g.step(); self.assertTrue(named(g.step(controls(dash=True)),'dash'))

    def test_charm_respawn_and_dropped_ttl(self):
        g=Game(scenario=quiet(charms=[{'id':'C1','pos':[5,0,0],'available':False,'respawn_ticks':2}],motes=[{'pos':[8,0,0],'kind':'dropped','ttl_ticks':2}]),night=2)
        g.step(); self.assertFalse(g.charms[0]['available']); self.assertEqual(len(g.motes),1)
        g.step(); self.assertTrue(g.charms[0]['available']); self.assertFalse(g.motes)

    def test_wind_schedule_and_pause(self):
        g=Game(scenario={'random_motes':False,'random_shades':False,'random_drifters':False},night=3)
        advance(g,1799); self.assertFalse(g.wind['active']); before=list(g.pos)
        g.step(); self.assertTrue(g.wind['active']); self.assertAlmostEqual(distance(before,g.pos),2/60)
        g.step(controls(pause=True)); old=g.snapshot(); advance(g,60)
        self.assertEqual(g.wind,old['wind']); self.assertEqual(g.sim_tick,old['sim_tick'])

    def test_maps_and_lantern_counts(self):
        self.assertEqual(World(1).lamps[1],[23.8,0,7.7])
        self.assertEqual([len(World(n).lamps) for n in (1,2,3)],[5,6,7])
        self.assertEqual([len(World(n).mote_points) for n in (1,2,3)],[24,24,30])
        self.assertEqual([len(World(n).fog_points) for n in (1,2,3)],[12,16,16])

    def test_bridge_and_island_edges(self):
        w=World(2); self.assertEqual(w.floor(35,2),0); self.assertIsNone(w.floor(35,2.01))
        self.assertEqual(w.floor(98,0),0); self.assertIsNone(w.floor(98.01,0))

    def test_launch_pad_locks_horizontal_input_and_lands_other_island(self):
        g=Game(scenario=quiet(player={'pos':[20,0,18]}),night=2)
        g.step(controls(move=[-1,0])); self.assertFalse(g.grounded); self.assertGreater(g.vel[0],0)
        advance(g,84,controls(move=[-1,0])); self.assertTrue(g.grounded)
        self.assertGreater(g.pos[0],42); self.assertIsNone(g.launch)

    def test_night3_surfaces_ramp_wall_and_tower(self):
        w=World(3)
        self.assertEqual(w.floor(0,7),6); self.assertEqual(w.floor(0,18),3); self.assertEqual(w.floor(0,-18),0)
        a=math.radians(30); self.assertAlmostEqual(w.floor(27*math.cos(a),27*math.sin(a)),1.5)
        self.assertTrue(w.blocked([0,0,24.1],[0,0,23.9]))
        self.assertTrue(w.blocked([2.1,6,0],[1.9,6,0]))

    def test_night3_pad_lands_on_top_tier(self):
        g=Game(scenario=quiet(player={'pos':[0,3,13]}),night=3)
        advance(g,55)
        self.assertTrue(g.grounded); self.assertAlmostEqual(g.pos[1],6)
        self.assertLess(math.hypot(g.pos[0],g.pos[2]),8)

    def test_palette_exact(self):
        self.assertEqual(PALETTE['sky'],'#0E1430'); self.assertEqual(PALETTE['coat'],'#E8E2D0')

    def test_new_spawn_cannot_be_picked_until_next_step(self):
        points=World(1).mote_points
        g=Game(scenario=dict(quiet(player={'pos':points[0]},motes=points[1:]),random_motes=True))
        advance(g,239); self.assertEqual(g.carried,0)
        g.step(); self.assertEqual(g.carried,0); self.assertEqual(len(g.motes),24)
        g.step(); self.assertEqual(g.carried,1)

    def test_recoil_moves_two_metres_in_sixty_steps(self):
        g=Game(scenario=quiet(shades=[{'pos':[0,.8,0]}]))
        g.step(); advance(g,60)
        self.assertAlmostEqual(g.shades[0]['pos'][0],2)

    def test_ground_level_scenario_shade_is_not_immobilized(self):
        g=Game(scenario=quiet(shades=[{'pos':[10,0,0]}])); advance(g,60)
        self.assertAlmostEqual(g.shades[0]['pos'][0],6)
        self.assertEqual(g.shades[0]['pos'][1],0)

    def test_dash_can_climb_a_ramp_without_climbing_wall(self):
        a=math.radians(30); r=28.
        g=Game(scenario=quiet(player={'pos':[r*math.cos(a),1,r*math.sin(a)]}),night=3)
        g.step(controls(move=[-math.cos(a),-math.sin(a)],dash=True))
        self.assertLess(math.hypot(g.pos[0],g.pos[2]),28)
        self.assertGreater(g.pos[1],1)

    def test_charm_can_be_collected_at_full_capacity(self):
        g=Game(scenario=quiet(player={'pos':[35,0,0],'carried':10}),night=2)
        self.assertTrue(named(g.step(),'charm_picked')); self.assertEqual(g.carried,10)

    def test_campaign_won_only_total_and_settings_roundtrip(self):
        from src.lantern_island.campaign import Campaign,Settings
        c=Campaign(); g=Game(); g.state='lost'; g.score=500
        self.assertFalse(c.complete(g)); self.assertEqual(c.total,0); self.assertFalse(c.next())
        g.state='won'; c.complete(g); c.complete(g); self.assertEqual(c.total,500)
        self.assertTrue(c.next()); self.assertEqual(c.night,2)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'settings.json'; s=Settings(path); s.volume=.3; s.sensitivity=.7; s.save()
            restored=Settings(path); self.assertEqual((restored.volume,restored.sensitivity),(.3,.7))
            path.write_text('{broken',encoding='utf-8'); self.assertEqual(Settings(path).volume,.5)


if __name__=='__main__': unittest.main()
