"""Exercise the actual desktop renderer/flows and measure real 1280x720 frames."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
# Mixer uses a test driver: audio routing and PCM creation are tested, not human hearing.
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from src.lantern_island.view import App,pg
from src.lantern_island.model import Game,DEFAULT_INPUT
from src.lantern_island.campaign import Settings
from src.lantern_island.maps import PALETTE


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--frames',type=int,default=180)
    parser.add_argument('--require-fps',type=float,default=30)
    args=parser.parse_args()
    if args.frames<1: parser.error('frames must be positive')
    target=Path(os.environ.get('LANTERN_PROOF_DIR',str(ROOT/'docs/proof/phase-4')))
    target.mkdir(parents=True,exist_ok=True)
    checks=[]; runs=[]
    with tempfile.TemporaryDirectory() as temp:
        settings_path=Path(temp)/'settings.json'
        app=App(settings_path=settings_path)
        try:
            assert app.screen=='menu'; app.draw(); pg.display.flip()
            pg.image.save(app.surface,str(target/'menu.png'))
            app.act('new'); assert app.screen=='intro'; app.act('play')
            for _ in range(60): app.step_once(dict(DEFAULT_INPUT,move=[0,1]))
            assert abs(app.game.pos[2]-6)<1e-6
            app.step_once(dict(DEFAULT_INPUT,jump=True)); assert app.game.pos[1]>0
            app.step_once(dict(DEFAULT_INPUT,dash=True)); assert app.game.dash_ticks==12
            checks.append('real desktop flow: menu, intro, movement, jump, dash')
            app.pause(); sim=app.game.sim_tick; wall=app.game.tick
            for _ in range(90): app.step_once()
            assert app.game.sim_tick==sim and app.game.tick==wall+90
            app.act('settings'); app.settings.volume=.3; app.settings.sensitivity=.65
            app.act('colorblind')
            app.act('back'); restored=Settings(settings_path)
            assert restored.volume==.3 and restored.sensitivity==.65 and restored.colorblind
            app.act('colorblind')
            app.resume(); assert app.screen=='playing' and app.game.state=='playing'
            event=pg.event.Event(pg.MOUSEMOTION,buttons=(0,0,1),rel=(10,0),pos=(640,360))
            old=app.yaw; app.handle_event(event); assert abs(app.yaw-old-6.5)<1e-6
            checks.append('pause freezes sim; settings persist; sensitivity changes mouse yaw')
            app.start_night(2,playing=True); app.game=Game(12,{'player':{'flames':0}},2)
            app.step_once(); assert app.screen=='score-entry' and app.campaign.total==0
            app.name_text='Quan_Test'; app.act('submit-score'); assert app.screen=='result'
            assert app.board.entries()[0]['score']==0
            app.act('retry'); assert app.game.night==2 and app.game.flames==3 and app.game.score==0
            app.campaign.scores={}
            for night in (1,2,3):
                app.start_night(night,playing=True)
                lamps=[{'id':'L'+str(i+1),'lit':True} for i in range(len(app.game.lanterns))]
                app.game=Game(12,{'lanterns':lamps,'time_left_s':1/60,'random_shades':False,'random_motes':False,'random_drifters':False},night)
                app.step_once(); assert app.screen=='result' and app.game.state=='won'
                app.act('next')
                assert app.screen==('dawn' if night==3 else 'intro')
            assert app.campaign.total>0
            app.draw(); pg.display.flip(); pg.image.save(app.surface,str(target/'dawn.png'))
            app.act('score'); app.name_text='Dawn_Test'; app.act('submit-score')
            assert app.screen=='leaderboard' and app.board_entries[0]['nights_won']==3
            assert app.board_entries[0]['score']==app.campaign.total
            app.draw(); pg.image.save(app.surface,str(target/'leaderboard.png'))
            app.act('settings'); app.act('reduced_motion'); app.act('large_text'); app.draw()
            assert min(app.canvas.rendered_font_sizes)>=22
            pg.image.save(app.surface,str(target/'settings-large.png'))
            app.act('bindings'); app.act('bind:jump')
            app.handle_event(pg.event.Event(pg.KEYDOWN,key=pg.K_w))
            assert app.pending_binding=='jump' and 'đang dùng' in app.binding_message
            app.handle_event(pg.event.Event(pg.KEYDOWN,key=pg.K_u))
            assert app.settings.bindings['jump']==['u']
            app.keys={pg.K_u}; assert app.controls()['jump']; app.keys.clear()
            app.draw(); pg.image.save(app.surface,str(target/'bindings-large.png'))
            app.act('bindings-default'); assert app.settings.bindings['jump']==['space']
            saved=Settings(settings_path); assert saved.reduced_motion and saved.large_text
            app.act('large_text'); app.act('reduced_motion'); app.act('bindings-back'); app.act('back')
            checks.append('loss/dawn score entry, won-only totals, durable board, rebind conflict/input/reset, saved reduced-motion and large text >=22px')
            assert app.audio and app.audio.available
            for name in ('mote_picked','lantern_lit','pulse','player_hit','jump','dash','won','lost','shade_spawned','countdown','wind'):
                app.audio.play(name)
            assert all(s.get_length()>0 for s in app.audio.sounds.values())
            checks.append('original PCM music and every required SFX routed to initialized dummy mixer')
            app.start_night(1,playing=True)
            app.game=Game(12,{'player':{'pos':[0,0,25],'carried':5},'time_left_s':30})
            app.canvas.text_cache.clear(); app.draw()
            rendered=list(app.canvas.text_cache)
            assert any(key[1].startswith('E — Nạp ánh sáng') for key in rendered)
            assert any(key[1]=='00:30' and key[2]==PALETTE['danger'] for key in rendered)
            pg.image.save(app.surface,str(target/'hud-danger.png'))
            app.game=Game(12); app.yaw=180; app.canvas.text_cache.clear(); app.draw()
            assert abs(app.scene.ambient-.15)<1e-9
            # Rounded standard map coordinates make L3 slightly closer than L1.
            # Isolate L1 as the only unlit lamp to test the offscreen-arrow path.
            for lamp in app.game.lanterns[1:]: lamp['lit']=True
            app.canvas.text_cache.clear(); app.draw()
            assert any(key[1].startswith('L1 ·') for key in app.canvas.text_cache)
            for lamp in app.game.lanterns: lamp['lit']=True
            app.draw(); assert abs(app.scene.ambient-.70)<1e-9
            checks.append('HUD near-E prompt, red30s timer, offscreen lantern arrow and ambient endpoints')
            # Phase3 accessibility/fuel visual fixture. All state changes below use real steps.
            app.start_night(1,playing=True); app.yaw=0
            app.game=Game(12,{'player':{'pos':[0,0,4.5],'carried':7,'successful_lights':3},
                             'lanterns':[{'id':'L1','pos':[0,0,6],'lit':True,'fuel':20},{'id':'L2','pos':[3,0,6]}],
                             'shades':[{'id':'S1','pos':[-3,.8,7],'state':'stunned','state_ticks_left':1000}],
                             'random_motes':False,'random_shades':False,'random_drifters':False,'time_left_s':30})
            app.act('colorblind'); before=app.game.snapshot()
            app.canvas.text_cache.clear(); app.draw()
            assert app.game.snapshot()==before
            assert app.scene.palette['outline']=='#00B3FF' and app.scene.palette['danger']=='#FFFFFF'
            assert any('⚠' in key[1] and key[2]=='#FFFFFF' for key in app.canvas.text_cache)
            assert any('7 / 16' in key[1] for key in app.canvas.text_cache)
            pg.image.save(app.surface,str(target/'colorblind-low-on.png'))
            for _ in range(30): app.step_once(dict(DEFAULT_INPUT))
            app.draw(); pg.image.save(app.surface,str(target/'colorblind-low-off.png'))
            app.step_once(dict(DEFAULT_INPUT,interact=True)); app.draw()
            assert app.game.protected(app.game.lanterns[0])
            pg.image.save(app.surface,str(target/'refueled.png'))
            app.act('colorblind')
            checks.append('v1.2 persisted accessible palette, white warning+icon, unchanged model, capacity16, low-fuel1Hz frames, deflated/torn unlit lamp and refuel restoration')
            app.start_night(1,playing=True)
            for _ in range(300): app.step_once(dict(DEFAULT_INPUT))
            assert len(app.notices)==2
            app.canvas.text_cache.clear(); app.draw()
            assert any('Bóng Mực xuất hiện' in key[1] for key in app.canvas.text_cache)
            assert min(app.canvas.rendered_font_sizes)>=18
            pg.image.save(app.surface,str(target/'shade-notice.png'))
            app.start_night(3,playing=True); app.game.sim_tick=1680
            app.canvas.text_cache.clear(); app.draw()
            assert any('Gió sắp thổi' in key[1] for key in app.canvas.text_cache)
            pg.image.save(app.surface,str(target/'wind-notice.png'))
            app.game=Game(12,{'time_left_s':10,'lanterns':[{'id':'L1','lit':True,'fuel':20}]},3)
            app.canvas.text_cache.clear(); app.draw()
            assert any('Còn 10 giây' in key[1] for key in app.canvas.text_cache)
            assert any('Đèn dầu dưới' in key[1] for key in app.canvas.text_cache)
            checks.append('visual spawn subtitles+edge arrows, wind prewarning, last10seconds and low-fuel indicators; all fonts>=18px')
            app.campaign.scores={}
            for night in (1,2,3):
                app.start_night(night,playing=True)
                app.game=Game(12,{'player':{'invuln_ticks':100000}},night)
                for _ in range(720): app.step_once(dict(DEFAULT_INPUT))
                assert app.game.state=='playing'
                for _ in range(10): app.draw(); pg.display.flip(); pg.event.pump()
                start=time.perf_counter()
                for frame in range(args.frames):
                    app.yaw=frame*.6
                    app.step_once(dict(DEFAULT_INPUT,move=[.2,.1]))
                    app.draw(); pg.display.flip(); pg.event.pump()
                elapsed=time.perf_counter()-start
                fps=args.frames/elapsed
                runs.append(dict(night=night,frames=args.frames,wall_seconds=elapsed,average_fps=fps,sim_tick=app.game.sim_tick,state=app.game.state,shades=len(app.game.shades)))
                pg.image.save(app.surface,str(target/('night%d.png'%night)))
                assert fps>=args.require_fps,('FPS requirement failed',night,fps)
            result=dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),platform=platform.platform(),python=sys.version,pygame=pg.version.ver,display_driver=pg.display.get_driver(),resolution=list(app.surface.get_size()),checks=checks,runs=runs,
                        limitations='Programmatic real framebuffer/flow test. FPS fixture has long invulnerability to prevent early death; standard map/spawns/rules unchanged. Dummy audio tests PCM/mixer routing, not human hearing. FPS includes logic/draw/flip/event pump, no limiter.')
            (target/'gui-smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            print('PASS: GUI campaign/settings/audio and all 3 nights >= %.0f FPS at 1280x720.'%args.require_fps)
            print(json.dumps(runs,indent=2))
        finally: pg.quit()
    return 0


if __name__=='__main__': sys.exit(main())
