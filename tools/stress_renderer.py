"""Additional worst-population rendering check, using only supported scenario overrides."""
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
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from src.lantern_island.view import App,pg
from src.lantern_island.model import Game,DEFAULT_INPUT


def main():
    results=[]
    with tempfile.TemporaryDirectory() as temp:
        app=App(settings_path=Path(temp)/'settings.json',audio=False)
        try:
            for night in (1,2,3):
                app.start_night(night,playing=True)
                lamps=[{'id':l['id'],'lit':True} for l in app.game.lanterns]
                shades=[{'pos':[p[0],p[1]+.8,p[2]],'state':'wander'} for p in app.game.world.fog_points[:{1:6,2:8,3:10}[night]]]
                app.game=Game(12,{'player':{'invuln_ticks':100000},'lanterns':lamps,'shades':shades,'wind_enabled':False},night)
                for _ in range(60): app.step_once(dict(DEFAULT_INPUT))
                assert len(app.game.shades)=={1:6,2:8,3:10}[night]
                start=time.perf_counter()
                for frame in range(180):
                    app.yaw=frame*.5; app.step_once(dict(DEFAULT_INPUT))
                    app.draw(); pg.display.flip(); pg.event.pump()
                elapsed=time.perf_counter()-start
                results.append(dict(night=night,frames=180,shades=len(app.game.shades),drifters=len(app.game.drifters),motes=len(app.game.motes),wall_seconds=elapsed,average_fps=180/elapsed))
            out=ROOT/'docs/proof/phase-3/renderer-stress.json'
            out.write_text(json.dumps(dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),resolution=[1280,720],platform=platform.platform(),driver=pg.display.get_driver(),results=results,
                                         fixture='Supported scenario sets maximum6/8/10 shades at standard fog points and all5/6/7 lamps fueled100; invulnerability/no wind prevent early death. Includes sim, draw, flip and event pump; real window, no limiter.'),indent=2)+'\n',encoding='utf-8')
            print(json.dumps(results,indent=2))
            assert all(r['average_fps']>=30 for r in results),'stress FPS below30'
        finally: pg.quit()


if __name__=='__main__': main()
