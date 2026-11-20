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
    target=Path(os.environ.get('LANTERN_PROOF_DIR',str(ROOT/'docs/proof/phase-2')))
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
            app.act('back'); restored=Settings(settings_path)
            assert restored.volume==.3 and restored.sensitivity==.65
            app.resume(); assert app.screen=='playing' and app.game.state=='playing'
            event=pg.event.Event(pg.MOUSEMOTION,buttons=(0,0,1),rel=(10,0),pos=(640,360))
            old=app.yaw; app.handle_event(event); assert abs(app.yaw-old-6.5)<1e-6
            checks.append('pause freezes sim; settings persist; sensitivity changes mouse yaw')
            app.start_night(2,playing=True); app.game=Game(12,{'player':{'flames':0}},2)
            app.step_once(); assert app.screen=='result' and app.campaign.total==0
            app.act('retry'); assert app.game.night==2 and app.game.flames==3 and app.game.score==0
            app.campaign.scores={}
            for night in (1,2,3):
                app.start_night(night,playing=True)
                lamps=[{'id':'L'+str(i+1),'lit':True} for i in range(len(app.game.lanterns))]
                app.game=Game(12,{'lanterns':lamps,'random_shades':False,'random_motes':False,'random_drifters':False},night)
                app.step_once(); assert app.screen=='result' and app.game.state=='won'
                app.act('next')
                assert app.screen==('dawn' if night==3 else 'intro')
            assert app.campaign.total>0
            app.draw(); pg.display.flip(); pg.image.save(app.surface,str(target/'dawn.png'))
            checks.append('loss/retry, all three result/next transitions, dawn and won-only totals')
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
            assert any(key[1].startswith('L1 ·') for key in app.canvas.text_cache)
            assert abs(app.scene.ambient-.15)<1e-9
            for lamp in app.game.lanterns: lamp['lit']=True
            app.draw(); assert abs(app.scene.ambient-.70)<1e-9
            checks.append('HUD near-E prompt, red30s timer, offscreen lantern arrow and ambient endpoints')
            app.campaign.scores={}
            for night in (1,2,3):
                app.start_night(night,playing=True)
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
                        limitations='Programmatic real framebuffer/flow test. Dummy audio driver tests PCM/mixer routing; not a human listening or independent play review. FPS is local hardware throughput including logic, draw, flip and event pump, without a frame limiter.')
            (target/'gui-smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            print('PASS: GUI campaign/settings/audio and all 3 nights >= %.0f FPS at 1280x720.'%args.require_fps)
            print(json.dumps(runs,indent=2))
        finally: pg.quit()
    return 0


if __name__=='__main__': sys.exit(main())
