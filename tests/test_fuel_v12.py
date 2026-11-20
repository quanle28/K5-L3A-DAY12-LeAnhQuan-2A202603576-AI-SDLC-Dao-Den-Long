import json
from pathlib import Path
import tempfile
import unittest
from src.lantern_island.model import Game,DEFAULT_INPUT,TUNING,distance
from src.lantern_island.campaign import Settings


def quiet(**kw): return dict(random_motes=False,random_shades=False,random_drifters=False,wind_enabled=False,**kw)
def controls(**kw): return dict(DEFAULT_INPUT,**kw)
def advance(g,n,c=None):
    events=[]
    for _ in range(n): events.extend(g.step(c))
    return events
def events(e,name): return [x for x in e if x['name']==name]


class FuelTests(unittest.TestCase):
    def test_manifest_fuel_and_score(self):
        expected=dict(fuel_max=100,fuel_decay_per_s=1.,fuel_per_mote=10,relight_cost=5,win_ratio=.6,
                      drain_per_s=5,low_fuel_threshold=30,capacity_max=20)
        for key,value in expected.items(): self.assertEqual(TUNING[key],value,key)
        self.assertEqual(TUNING['score']['per_mote'],5)
        self.assertEqual(TUNING['score']['per_second_left'],0)

    def test_setup_defaults_have_no_score_or_capacity_gain(self):
        g=Game(scenario=quiet(lanterns=[{'id':'L1','lit':True}]))
        l=g.lanterns[0]
        self.assertEqual(l['fuel_units'],6000); self.assertTrue(l['ever_lit'])
        self.assertEqual((l['relit_count'],g.capacity,g.score,g.successful_lights),(0,10,0,0))
        self.assertEqual(g.events,[])

    def test_decay_is_exact_and_out_once(self):
        g=Game(scenario=quiet(lanterns=[{'id':'L1','lit':True}]))
        advance(g,5999); self.assertEqual(g.lanterns[0]['fuel_units'],1); self.assertTrue(g.lanterns[0]['lit'])
        out=g.step(); self.assertEqual(len(events(out,'lantern_out')),1)
        l=g.lanterns[0]
        self.assertEqual((l['lit'],l['fuel_units'],l['deposited'],l['ever_lit']),(False,0,0,True))
        self.assertFalse(events(advance(g,10),'lantern_out'))

    def test_snapshot_rounding_does_not_define_full_or_low(self):
        g=Game(scenario=quiet(lanterns=[{'id':'L1','lit':True,'fuel':99.96}]))
        self.assertEqual(g.fuel(g.lanterns[0]),100.0)
        self.assertTrue(g.accepts(g.lanterns[0]))
        g=Game(scenario=quiet(lanterns=[{'id':'L1','lit':True,'fuel':30}]))
        self.assertTrue(g.protected(g.lanterns[0])); g.step()
        self.assertEqual(g.fuel(g.lanterns[0]),30.0)
        self.assertFalse(g.protected(g.lanterns[0]))

    def test_refuel_ceil_uses_unrounded_post_decay_fuel(self):
        g=Game(scenario=quiet(player={'carried':5},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':90}]))
        e=g.step(controls(interact=True))
        self.assertEqual(events(e,'refuel')[0]['data'],dict(lantern_id='L1',amount=2,fuel=100.0))
        self.assertEqual((g.carried,g.score,g.successful_lights),(3,10,0))
        self.assertFalse(events(e,'deposit')); self.assertFalse(events(e,'lantern_lit'))

    def test_truly_full_lamp_skipped_in_nearest_selection(self):
        g=Game(scenario=quiet(player={'carried':5},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True}, {'id':'L2','pos':[1,0,0]}]))
        # Invoke the interaction stage at the exact setup state, before tick decay.
        g._deposit()
        self.assertEqual(events(g.events,'deposit')[0]['data']['lantern_id'],'L2')
        self.assertEqual(g.score,25); self.assertFalse(events(g.events,'refuel'))
        full=Game(scenario=quiet(player={'carried':5},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True}]))
        full._deposit(); self.assertEqual(full.events,[]); self.assertEqual(full.score,0)

    def test_refuel_and_unlit_tie_uses_id(self):
        g=Game(scenario=quiet(player={'carried':1},lanterns=[{'id':'L1','pos':[-1,0,0],'lit':True,'fuel':50},{'id':'L2','pos':[1,0,0]}]))
        e=g.step(controls(interact=True)); self.assertEqual(events(e,'refuel')[0]['data']['lantern_id'],'L1')

    def test_first_light_then_pickup_uses_new_capacity_next_step(self):
        g=Game(scenario=quiet(motes=[[0,0,0]]*13,lanterns=[{'id':'L1','pos':[0,0,0]}]))
        e=g.step(controls(interact=True)); self.assertEqual(len(events(e,'mote_picked')),10)
        self.assertEqual(events(e,'lantern_lit')[0]['data'],dict(lantern_id='L1',relight=False))
        self.assertEqual((g.capacity,g.carried,g.score),(12,0,150))
        g.step(); self.assertEqual(g.carried,3)

    def test_relight_cost_reward_and_counter(self):
        g=Game(scenario=quiet(player={'carried':5},lanterns=[{'id':'L1','pos':[0,0,0],'ever_lit':True}]))
        e=g.step(controls(interact=True)); l=g.lanterns[0]
        self.assertEqual(events(e,'lantern_lit')[0]['data'],dict(lantern_id='L1',relight=True))
        self.assertEqual((g.score,g.capacity,l['relit_count'],l['fuel_units']),(65,12,1,6000))
        l['fuel_units']=1; g.step(); g.carried=5; g.step(controls(interact=True))
        self.assertEqual((g.successful_lights,g.capacity,l['relit_count'],g.score),(2,14,2,130))

    def test_capacity_scenario_is_applied_before_carried_and_caps_at_20(self):
        g=Game(scenario=quiet(player={'successful_lights':5,'carried':20}))
        self.assertEqual(g.snapshot()['player']['capacity'],20)
        self.assertEqual(Game(scenario=quiet(player={'successful_lights':500})).capacity,20)
        self.assertEqual(Game().capacity,10)
        with self.assertRaises(ValueError): Game(scenario=quiet(player={'successful_lights':-1}))

    def test_partial_relight_remembers_progress(self):
        g=Game(scenario=quiet(player={'carried':2},lanterns=[{'id':'L1','pos':[0,0,0],'ever_lit':True}]))
        g.step(controls(interact=True)); self.assertFalse(g.lanterns[0]['lit']); self.assertEqual(g.lanterns[0]['deposited'],2)
        g.step(); g.carried=3; g.step(controls(interact=True)); self.assertTrue(g.lanterns[0]['lit'])

    def test_stack_drain_and_global_sim_tick_event_cadence(self):
        shades=[{'id':name,'pos':[0,.8,0],'state':'drain','target_lantern_id':'L1'} for name in ('S2','S1')]
        g=Game(scenario=quiet(player={'pos':[30,0,0]},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],shades=shades))
        e=advance(g,60); self.assertEqual(g.lanterns[0]['fuel_units'],540)
        drains=events(e,'fuel_drain'); self.assertEqual(len(drains),2)
        self.assertEqual([x['data']['shade_id'] for x in drains],['S1','S2'])
        self.assertTrue(all(x['tick']==60 and x['data']['fuel']==9.0 for x in drains))

    def test_wander_prioritizes_weak_lit_then_lowest_id(self):
        lamps=[{'id':'L1','pos':[1,0,0],'lit':True,'fuel':20},{'id':'L2','pos':[-1,0,0],'lit':True,'fuel':20},{'id':'L3','pos':[.1,0,0]}]
        g=Game(scenario=quiet(player={'pos':[30,0,0]},lanterns=lamps,shades=[{'pos':[0,.8,0],'state':'wander'}]))
        g.step(); self.assertEqual(g.shades[0]['state'],'drain'); self.assertEqual(g.shades[0]['target_lantern_id'],'L1')
        self.assertEqual(g.lanterns[0]['fuel_units'],1199)  # First drain is next step2.
        g.step(); self.assertEqual(g.lanterns[0]['fuel_units'],1193)

    def test_chase_does_not_switch_to_weak_lamp(self):
        g=Game(scenario=quiet(player={'pos':[10,0,0]},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],shades=[{'pos':[0,.8,0],'state':'chase'}]))
        g.step(); self.assertEqual(g.shades[0]['state'],'chase'); self.assertIsNone(g.shades[0]['target_lantern_id'])

    def test_drain_exits_for_near_player_or_out_or_distance(self):
        for player,lit,pos,expected in [([6,0,0],True,[0,.8,0],'chase'),([30,0,0],False,[0,.8,0],'wander'),([30,0,0],True,[3,.8,0],'wander')]:
            g=Game(scenario=quiet(player={'pos':player},lanterns=[{'id':'L1','pos':[0,0,0],'lit':lit,'fuel':20 if lit else 0,'ever_lit':True}],shades=[{'pos':pos,'state':'drain','target_lantern_id':'L1'}]))
            g.step(); self.assertEqual(g.shades[0]['state'],expected)

    def test_refuel_restores_safe_ejection_no_hit_in_30_ticks(self):
        g=Game(scenario=quiet(player={'carried':2},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],shades=[{'pos':[1,.8,0],'state':'drain','target_lantern_id':'L1'}]))
        e=g.step(controls(interact=True)); self.assertTrue(events(e,'refuel'))
        self.assertTrue(g.protected(g.lanterns[0])); self.assertEqual(g.flames,3)
        advance(g,29); self.assertGreaterEqual(distance(g.shades[0]['pos'],[0,0,0]),6-1e-6)
        self.assertEqual(g.flames,3)

    def test_30_exactly_safe_below_30_allows_entry(self):
        for initial,protected in [(30+1/60,True),(30,False)]:
            g=Game(scenario=quiet(player={'pos':[30,0,0]},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':initial}],shades=[{'pos':[6.01,.8,0],'state':'wander'}]))
            g.step(); d=distance(g.shades[0]['pos'],[0,0,0])
            self.assertEqual(g.protected(g.lanterns[0]),protected)
            self.assertTrue(d>=6 if protected else d<6)

    def test_pulse_drain_awards_total15_then_wakes_wander(self):
        g=Game(scenario=quiet(player={'carried':3},lanterns=[{'id':'L1','pos':[3,0,0],'lit':True,'fuel':20}],shades=[{'pos':[3,.8,0],'state':'drain','target_lantern_id':'L1'}]))
        g.step(controls(pulse=True)); self.assertEqual(g.score,15); self.assertEqual(g.shades[0]['state'],'stunned')
        advance(g,120); self.assertEqual(g.shades[0]['state'],'wander')

    def test_pause_freezes_fuel_drain_and_cadence_uses_sim_ticks(self):
        g=Game(scenario=quiet(player={'pos':[30,0,0]},lanterns=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':20}],shades=[{'pos':[0,.8,0],'state':'drain','target_lantern_id':'L1'}]))
        g.step(controls(pause=True)); advance(g,60)
        self.assertEqual(g.lanterns[0]['fuel_units'],1200)
        e=g.step(controls(pause=True))+advance(g,59)
        drain=events(e,'fuel_drain'); self.assertEqual(len(drain),1)
        self.assertEqual(drain[0]['tick'],121); self.assertEqual(g.sim_tick,60)

    def test_all_lit_never_ends_early(self):
        lamps=[{'id':'L'+str(i),'lit':True} for i in range(1,6)]
        g=Game(scenario=quiet(lanterns=lamps)); e=advance(g,600)
        self.assertEqual(g.state,'playing'); self.assertFalse(events(e,'game_over'))

    def test_dawn_thresholds_and_new_bonus_all_nights(self):
        for n,needed,total in [(1,3,5),(2,4,6),(3,5,7)]:
            for count in (needed-1,needed):
                lamps=[{'id':'L'+str(i),'lit':True} for i in range(1,count+1)]
                g=Game(scenario=quiet(lanterns=lamps,time_left_s=1/60),night=n); e=g.step()
                expected='won' if count==needed else 'lost'
                self.assertEqual(g.state,expected)
                self.assertEqual(e[-1]['data']['reason'],'dawn_survived' if expected=='won' else 'dawn')
                self.assertEqual(g.score,count*149+150 if expected=='won' else 0)

    def test_expiry_at_dawn_loses_but_same_tick_relight_can_win(self):
        lamps=[{'id':'L1','pos':[0,0,0],'lit':True,'fuel':1/60},{'id':'L2','lit':True},{'id':'L3','lit':True}]
        lost=Game(scenario=quiet(lanterns=lamps,time_left_s=1/60)); lost.step(); self.assertEqual(lost.state,'lost')
        g=Game(scenario=quiet(player={'carried':5},lanterns=lamps,time_left_s=1/60))
        e=g.step(controls(interact=True)); self.assertEqual(g.state,'won'); self.assertEqual(g.score,663)
        self.assertEqual([x['name'] for x in e if x['name'] in ('lantern_out','lantern_lit','game_over')],['lantern_out','lantern_lit','game_over'])

    def test_no_flames_beats_dawn_survival(self):
        lamps=[{'id':'L'+str(i),'lit':True} for i in range(1,6)]
        g=Game(scenario=quiet(player={'pos':[41,-10,0],'flames':1},lanterns=lamps,time_left_s=1/60))
        g.step(); self.assertEqual(g.state,'lost'); self.assertEqual(g.events[-1]['data']['reason'],'no_flames')

    def test_new_scenario_validation(self):
        for data in (quiet(lanterns=[{'id':'L1','lit':True,'fuel':101}]),quiet(lanterns=[{'id':'L1','ever_lit':1}]),quiet(shades=[{'pos':[0,0,0],'state':'drain','target_lantern_id':'L99'}])):
            with self.subTest(data=data),self.assertRaises(ValueError): Game(scenario=data)

    def test_colorblind_settings_persist_and_old_settings_upgrade(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'settings.json'
            path.write_text(json.dumps(dict(volume=.3,sensitivity=.4)),encoding='utf-8')
            settings=Settings(path); self.assertFalse(settings.colorblind)
            settings.colorblind=True; settings.save()
            new=Settings(path); self.assertTrue(new.colorblind); self.assertEqual(new.volume,.3)


if __name__=='__main__': unittest.main()
