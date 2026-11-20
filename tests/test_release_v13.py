"""Release regressions: measured statistics, isolated bench, durable user data."""
import contextlib
import io
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from src.lantern_island.performance import frame_statistics,orbit_camera,benchmark_game,benchmark_step,random_controls,run_soak
from src.lantern_island.leaderboard import Leaderboard,valid_name,validate_entry,timestamp
from src.lantern_island.campaign import Settings,DEFAULT_BINDINGS,Campaign

ROOT=Path(__file__).resolve().parents[1]

class ReleaseTests(unittest.TestCase):
    def test_statistics_slowest_one_percent_and_percentile(self):
        s=frame_statistics([10]*198+[40,60])
        self.assertEqual(s['frames'],200)
        self.assertAlmostEqual(s['avg_fps'],200000/2080)
        self.assertEqual(s['p1_low_fps'],20)
        self.assertEqual(s['frame_ms_p95'],10)
        self.assertAlmostEqual(frame_statistics([10,20])['frame_ms_p95'],19.5)

    def test_statistics_reject_invalid(self):
        for values in ([],[0],[-1],[float('nan')],[float('inf')]):
            with self.assertRaises(ValueError): frame_statistics(values)

    def test_orbit_exact_geometry_and_period(self):
        for t,expected in [(0,[30,15,0]),(3.75,[0,15,30]),(7.5,[-30,15,0]),(15,[30,15,0])]:
            eye,target=orbit_camera(t)
            for a,b in zip(eye,expected): self.assertAlmostEqual(a,b)
            self.assertEqual(target,[0,0,0])

    def test_benchmark_scene_and_disabled_rules(self):
        game=benchmark_game(42); other=benchmark_game(42)
        self.assertEqual(game.snapshot(),other.snapshot())
        self.assertEqual(len(game.shades),200); self.assertEqual(len(game.motes),100)
        self.assertEqual(sum(l['lit'] for l in game.lanterns),3)
        before=[list(s['pos']) for s in game.shades]
        for _ in range(600): benchmark_step(game)
        self.assertEqual(len(game.shades),200); self.assertEqual(len(game.motes),100)
        self.assertEqual([game.fuel(l) for l in game.lanterns[:3]],[100]*3)
        self.assertTrue(all(s['state']=='wander' for s in game.shades))
        self.assertNotEqual(before,[s['pos'] for s in game.shades])
        self.assertEqual(game.pos,[0,0,0]); self.assertEqual(game.flames,3)
        self.assertEqual(game.state,'playing'); self.assertEqual(game.time_left,230)

    def test_seeded_controls_persist_direction_and_rates(self):
        rng=random.Random(7); other=random.Random(7); move=[0,0]; other_move=[0,0]; counts=dict(jump=0,dash=0,pulse=0,interact=0)
        previous=None
        for tick in range(30000):
            c,move=random_controls(rng,tick,move); d,other_move=random_controls(other,tick,other_move)
            self.assertEqual(c,d)
            if tick%30: self.assertEqual(move,previous)
            self.assertAlmostEqual(math.hypot(*move),1)
            previous=move
            for key in counts: counts[key]+=c[key]
        for key,p in [('jump',.05),('dash',.03),('pulse',.02),('interact',.1)]: self.assertLess(abs(counts[key]/30000-p),.01)

    def test_soak_same_process_order_real_results(self):
        with tempfile.TemporaryDirectory() as temp,contextlib.redirect_stdout(io.StringIO()):
            result=run_soak(7,3,Path(temp)/'soak.json')
        import os
        self.assertEqual(result['pid'],os.getpid()); self.assertEqual(result['seeds'],[7,8,9])
        self.assertEqual(result['night_order'],[1,2,3]); self.assertEqual(result['crashes'],0)
        self.assertTrue(all(s in ('won','lost') for s in result['results']))
        self.assertTrue(all(t>0 for t in result['sim_ticks']))

    def test_names_unicode_and_invalid(self):
        for value in ('abc','Quan_123','Mây','Nguyễn_Quân'): self.assertTrue(valid_name(value))
        for value in ('ab','a'*13,'abc def','a/b','<script>',None): self.assertFalse(valid_name(value))

    def test_top10_sort_tie_timezone_and_reopen(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'board.json'; board=Leaderboard(path)
            for i in range(12): board.add('user'+str(i),i,1,42,'2026-11-20T10:00:00+07:00')
            board.add('later',100,2,42,'2026-11-20T05:00:00+00:00')
            board.add('earlier',100,2,42,'2026-11-20T10:00:00+07:00')
            entries=Leaderboard(path).entries()
            self.assertEqual(len(entries),10); self.assertEqual([e['name'] for e in entries[:2]],['earlier','later'])
            self.assertTrue(all(entries[i]['score']>=entries[i+1]['score'] for i in range(9)))
            self.assertEqual(entries[0]['seed'],42); self.assertIsNotNone(timestamp(entries[0]['achieved_at']).utcoffset())

    def test_entry_validation(self):
        entry=dict(name='Quan',score=1,nights_won=1,seed=42,achieved_at='2026-11-20T00:00:00+00:00')
        for field,value in [('score',-1),('score',True),('nights_won',4),('seed',True),('achieved_at','2026-11-20T00:00:00')]:
            with self.assertRaises(ValueError): validate_entry(dict(entry,**{field:value}))

    def test_corrupt_board_backup_and_export_error(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'leaderboard.json'; path.write_text('{broken')
            board=Leaderboard(path)
            with self.assertRaises(ValueError): board.export(Path(temp)/'export.json')
            board.add('Quan',0,0,7)
            self.assertEqual(len(list(Path(temp).glob('*.corrupt-*'))),1)
            self.assertEqual(len(board.entries()),1)

    def test_export_cli_without_gpu_or_user_data(self):
        with tempfile.TemporaryDirectory() as temp:
            Leaderboard(Path(temp)/'leaderboard.json').add('Quan',500,2,42)
            out=Path(temp)/'export.json'
            p=subprocess.run([sys.executable,str(ROOT/'game.py'),'--data-dir',temp,'--export-leaderboard',str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(out.read_text())['entries'][0]['score'],500)

    def test_all_bindings_persist_conflict_restore_and_old_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'settings.json'
            path.write_text(json.dumps(dict(volume=.3,sensitivity=.6,colorblind=True)))
            settings=Settings(path); self.assertTrue(settings.colorblind)
            self.assertEqual(settings.bindings,DEFAULT_BINDINGS)
            for action,key in zip(DEFAULT_BINDINGS,['i','k','j','l','u','o','h','g','t']): settings.rebind(action,key)
            with self.assertRaises(ValueError): settings.rebind('jump','i')
            settings.reduced_motion=True; settings.large_text=True; settings.save()
            restored=Settings(path); self.assertTrue(restored.large_text and restored.reduced_motion)
            self.assertEqual(restored.bindings,settings.bindings)
            restored.restore_bindings(); self.assertEqual(Settings(path).bindings,DEFAULT_BINDINGS)

    def test_loss_score_excluded_from_campaign(self):
        from src.lantern_island.model import Game
        campaign=Campaign(); won=Game(12); won.state='won'; won.score=123; campaign.complete(won)
        lost=Game(12,night=2); lost.state='lost'; lost.score=999; campaign.complete(lost)
        self.assertEqual(campaign.total,123); self.assertEqual(len(campaign.scores),1)
