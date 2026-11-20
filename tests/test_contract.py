import copy
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from game import load_json, run_headless
from src.lantern_island.model import DEFAULT_INPUT, Game, TUNING, distance, validate_inputs

ROOT = Path(__file__).resolve().parents[1]


def empty(**kwargs):
    return dict(random_motes=False, random_shades=False, **kwargs)


def button(name, value=True, **kwargs):
    return dict(DEFAULT_INPUT, **{name: value}, **kwargs)


def records(game, frames=(), ticks=60, every=10):
    stream = io.StringIO()
    run_headless(game, list(frames), ticks, every, stream)
    return [json.loads(line) for line in stream.getvalue().splitlines()]


class ContractTests(unittest.TestCase):
    def test_manifest_is_runtime_source(self):
        contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["contract_version"], "1.0")
        self.assertEqual(contract["tuning"], TUNING)
        self.assertEqual(len(Game().lanterns), 5)

    def test_zero_ticks_and_tick_zero(self):
        r = records(Game(scenario=empty()), ticks=0)
        self.assertEqual([e["type"] for e in r], ["snapshot", "end"])
        self.assertEqual(r[0]["player"]["pos"], [0, 0, 0])
        self.assertEqual(r[-1]["ticks"], 0)

    def test_fixed_steps_and_time(self):
        r = records(Game(scenario=empty()), ticks=123, every=10)
        self.assertEqual([e["tick"] for e in r if e["type"] == "snapshot"], list(range(0, 121, 10)))
        self.assertEqual(r[-2]["time_left_s"], 298)
        self.assertEqual(r[-1]["ticks"], 123)
        self.assertEqual(r[-2]["sim_tick"], 120)

    def test_move_preserves_magnitude(self):
        game = Game(scenario=empty())
        for _ in range(60): game.step(dict(DEFAULT_INPUT, move=[.5, 0]))
        self.assertAlmostEqual(game.pos[0], 3)

    def test_camera_rotation_and_diagonal_normalization(self):
        game = Game(scenario=empty())
        for _ in range(60): game.step(dict(DEFAULT_INPUT, move=[0, 1], cam_yaw_deg=90))
        self.assertAlmostEqual(game.pos[0], 6)
        self.assertAlmostEqual(game.pos[2], 0)
        diagonal = Game(scenario=empty())
        for _ in range(60): diagonal.step(dict(DEFAULT_INPUT, move=[1, 1]))
        self.assertAlmostEqual(math.hypot(diagonal.pos[0], diagonal.pos[2]), 6)

    def test_partial_frame_persistence(self):
        game = Game(scenario=empty())
        frames = [{"tick": 0, "move": [0, 1]}, {"tick": 10, "cam_yaw_deg": 90}, {"tick": 20, "move": [0, 0]}]
        records(game, frames, ticks=30)
        self.assertAlmostEqual(game.pos[0], 1)
        self.assertAlmostEqual(game.pos[2], 1)

    def test_pickup_inclusive_xz_and_capacity(self):
        game = Game(scenario=empty(motes=[[1.2, 8, 0]] * 14))
        events = game.step()
        self.assertEqual(game.carried, 12)
        self.assertEqual(len(game.motes), 2)
        self.assertEqual(game.score, 120)
        self.assertEqual(len(events), 12)
        self.assertTrue(all(e["tick"] == 1 for e in events))
        self.assertEqual(game.step(), [])

    def test_pickup_outside_radius(self):
        game = Game(scenario=empty(motes=[[1.201, 0, 0]]))
        game.step()
        self.assertEqual(game.carried, 0)

    def test_partial_deposit_and_edge_trigger(self):
        game = Game(scenario=empty(player={"carried": 4}, lanterns=[{"id": "L1", "pos": [2.5, 0, 0]}]))
        events = game.step(button("interact"))
        self.assertEqual(events[0]["data"], dict(lantern_id="L1", amount=4, deposited=4))
        self.assertFalse(game.lanterns[0]["lit"])
        game.carried = 6
        self.assertEqual(game.step(button("interact")), [])
        game.step()
        events = game.step(button("interact"))
        self.assertEqual([e["name"] for e in events], ["deposit", "lantern_lit"])
        self.assertEqual(game.score, 100)
        self.assertTrue(game.lanterns[0]["lit"])

    def test_deposit_only_remaining_and_nearest(self):
        game = Game(scenario=empty(player={"carried": 12}, lanterns=[{"id": "L1", "pos": [1,0,0], "deposited": 8}, {"id": "L2", "pos": [2,0,0]}]))
        game.step(button("interact"))
        self.assertEqual(game.carried, 10)
        self.assertEqual(game.lanterns[1]["deposited"], 0)

    def test_far_or_empty_deposit_has_no_event(self):
        for data in (empty(player={"carried": 12}), empty(lanterns=[{"id":"L1", "pos":[0,0,0]}])):
            self.assertEqual(Game(scenario=data).step(button("interact")), [])

    def test_scenario_updates_by_id_without_score(self):
        game = Game(scenario=empty(lanterns=[{"id":"L3", "pos":[2,0,3], "lit":True}]))
        self.assertEqual(len(game.lanterns), 5)
        self.assertEqual(game.lanterns[2]["pos"], [2,0,3])
        self.assertEqual(game.score, 0)
        self.assertEqual(game.events, [])
        self.assertEqual(game.lanterns[0]["deposited"], 0)

    def test_explicit_empty_lists_override_defaults(self):
        game = Game(scenario={"motes": [], "shades": []})
        self.assertEqual(len(game.motes), 0)
        self.assertEqual(len(game.shades), 0)

    def test_pulse_cost_push_stun_inclusive_and_no_hit(self):
        game = Game(scenario=empty(player={"carried":3}, shades=[{"id":"test", "pos":[5,0,0]}, {"id":"touch", "pos":[0,0,0]}, {"id":"far", "pos":[5.001,0,0]}]))
        events=game.step(button("pulse"))
        self.assertEqual(events[0]["data"]["stunned_ids"], ["test", "touch"])
        self.assertEqual(game.carried, 0)
        self.assertEqual(game.shades[0]["pos"][0], 8)
        self.assertEqual(game.shades[0]["state"], "stunned")
        self.assertEqual(game.flames, 3)
        self.assertEqual(game.score, 40)
        for _ in range(179): game.step()
        self.assertEqual(game.shades[0]["state"], "stunned")
        game.step()
        self.assertEqual(game.shades[0]["state"], "chase")

    def test_pulse_cooldown_and_edge(self):
        game=Game(scenario=empty(player={"carried":12}))
        game.step(button("pulse"))
        game.step(button("pulse"))
        self.assertEqual(game.carried, 9)
        game.step()
        self.assertEqual(game.step(button("pulse")), [])
        for _ in range(86): game.step()
        self.assertEqual(game.tick, 90)
        game.step(button("pulse"))
        self.assertEqual(game.carried, 6)

    def test_insufficient_pulse_does_not_spend(self):
        game=Game(scenario=empty(player={"carried":2}))
        self.assertEqual(game.step(button("pulse")), [])
        self.assertEqual(game.carried, 2)

    def test_shade_chases_at_declared_speed(self):
        game=Game(scenario=empty(shades=[{"pos":[10,0,0]}]))
        for _ in range(60): game.step()
        self.assertAlmostEqual(game.shades[0]["pos"][0], 8)

    def test_hit_drop_invulnerability_and_loss(self):
        game=Game(scenario=empty(player={"carried":12}, shades=[{"pos":[0,0,0]}, {"pos":[0,0,0]}]))
        e=game.step()
        self.assertEqual(e[0]["data"], dict(by="shade", flames=2, dropped=3))
        for _ in range(119): game.step()
        self.assertEqual(game.flames, 2)
        game.step()
        self.assertEqual(game.flames, 1)
        for _ in range(120): game.step()
        self.assertEqual(game.state, "lost")
        self.assertEqual(game.events[-1]["data"], dict(result="lost",reason="no_flames"))

    def test_safe_zone_excludes_shades_and_damage(self):
        game=Game(scenario=empty(lanterns=[{"id":"L1", "pos":[0,0,0], "lit":True}],shades=[{"pos":[6,0,0]}]))
        for _ in range(300): game.step()
        self.assertGreaterEqual(distance(game.shades[0]["pos"], [0,0,0]), 4)
        self.assertEqual(game.flames, 3)

    def test_jump_grounded_edge_trigger(self):
        game=Game(scenario=empty())
        game.step(button("jump"))
        self.assertGreater(game.pos[1], 0)
        for _ in range(120): game.step(button("jump"))
        self.assertEqual(game.pos[1], 0)
        game.step()
        game.step(button("jump"))
        self.assertGreater(game.pos[1], 0)

    def test_island_boundary_has_no_fall_penalty(self):
        game=Game(scenario=empty())
        for _ in range(500): game.step(dict(DEFAULT_INPUT, move=[1,0]))
        self.assertAlmostEqual(game.pos[0], 32)
        self.assertEqual(game.flames, 3)

    def test_dawn_stops_exactly(self):
        r=records(Game(scenario=empty(time_left_s=1)),ticks=1000)
        self.assertEqual(r[-1]["ticks"], 60)
        self.assertEqual(r[-1]["state"], "lost")
        self.assertEqual([e for e in r if e.get("name")=="game_over"][0]["data"]["reason"], "dawn")

    def test_fractional_dawn_time_obeys_exact_formula(self):
        game=Game(scenario=empty(time_left_s=.01))
        game.step()
        self.assertEqual(game.snapshot()['time_left_s'], .01-1/60)

    def test_setup_preserves_shade_position_and_has_no_events(self):
        game=Game(scenario=empty(lanterns=[{'id':'L1','pos':[0,0,0],'lit':True}],shades=[{'id':'inside','pos':[0,0,0]}]))
        self.assertEqual(game.snapshot()['shades'][0]['pos'],[0,0,0])
        self.assertEqual(game.events,[])
        game.step()
        self.assertGreaterEqual(distance(game.shades[0]['pos'],[0,0,0]),4)

    def test_win_bonus_and_early_stop(self):
        lamps=[{"id":"L"+str(i),"lit":True} for i in range(1,5)]
        lamps.append({"id":"L5","pos":[0,0,0],"deposited":9})
        game=Game(scenario=empty(player={"carried":1},lanterns=lamps,time_left_s=10))
        r=records(game,[{"tick":0,"interact":True}],ticks=500,every=1)
        self.assertEqual(r[-1],dict(type="end",ticks=1,state="won",score=100+18+150))
        game.step()
        self.assertEqual(game.tick, 1)

    def test_default_spawn_and_seed_determinism(self):
        a,b=io.StringIO(),io.StringIO()
        # Safe central lamp allows a long run including procedural spawns.
        scenario={"lanterns":[{"id":"L1","pos":[0,0,0],"lit":True}]}
        run_headless(Game(125,scenario),[],1500,10,a)
        run_headless(Game(125,scenario),[],1500,10,b)
        self.assertEqual(a.getvalue(), b.getvalue())
        self.assertIn('"shade_spawned"', a.getvalue())
        self.assertNotEqual(Game(125).snapshot(), Game(126).snapshot())

    def test_rounds_coordinates_to_three_decimals(self):
        game=Game(scenario=empty(player={"pos":[.123456,0,-.987654]}))
        self.assertEqual(game.snapshot()["player"]["pos"],[.123,0,-.988])

    def test_invalid_input_formats(self):
        bad=[{}, {"frames":None}, {"frames":[{"tick":0},{"tick":0}]},
             {"frames":[{"tick":2},{"tick":1}]}, {"frames":[{"tick":-1}]},
             {"frames":[{"tick":True}]}, {"frames":[{"tick":0,"pulse":1}]},
             {"frames":[{"tick":0,"move":[2,0]}]}, {"frames":[{"tick":0,"move":[0]}]},
             {"frames":[{"tick":0,"cam_yaw_deg":float("nan")}]},
             {"frames":[{"tick":0,"oops":True}]}]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ValueError): validate_inputs(data)

    def test_invalid_scenario_formats(self):
        bad=[[], {"player":None}, {"player":{"pos":[0,0]}}, {"motes":None},
             {"shades":[{"pos":[0,0,0],"id":3}]}, {"shades":[{"pos":[0,0,0],"id":"X"}]*2},
             {"random_motes":0}, {"player":{"carried":13}}, {"time_left_s":-1},
             {"lanterns":[{"id":"L6"}]}, {"lanterns":[{"id":"L1","lit":1}]},
             {"lanterns":[{"id":"L1","deposited":11}]}, {"unknown":1}]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ValueError): Game(scenario=data)

    def test_cli_process_output_and_bad_file_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"out.jsonl"
            bad=Path(tmp)/"bad.json"
            bad.write_text('{"frames": [{"tick":0,"pulse":"yes"}]}',encoding="utf-8")
            cmd=[sys.executable,str(ROOT/"game.py"),"--headless","--seed","12","--night","1","--ticks","2","--out",str(out)]
            result=subprocess.run(cmd,capture_output=True,text=True,cwd=ROOT)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(json.loads(out.read_text().splitlines()[-1])["ticks"],2)
            result=subprocess.run(cmd+["--inputs",str(bad)],capture_output=True,text=True,cwd=ROOT)
            self.assertEqual(result.returncode,2)
            self.assertIn("Invalid inputs/scenario", result.stderr)
            bad.write_text('{"player":',encoding="utf-8")
            result=subprocess.run(cmd+["--scenario",str(bad)],capture_output=True,text=True,cwd=ROOT)
            self.assertEqual(result.returncode,2)

    def test_json_duplicate_keys_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"data.json"
            for data in ('{"frames":[],"frames":[]}', '{"time_left_s":NaN}'):
                path.write_text(data,encoding="utf-8")
                with self.assertRaises(ValueError): load_json(path)


if __name__=="__main__": unittest.main()
