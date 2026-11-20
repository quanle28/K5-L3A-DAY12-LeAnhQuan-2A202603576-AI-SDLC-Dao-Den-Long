"""Programmatic test of our Tk application, not OS-level UI automation."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import time
import tkinter as tk

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.lantern_island.view import App
from src.lantern_island.model import Game


def main():
    root=tk.Tk()
    checks=[]
    try:
        app=App(root,schedule=False)
        root.update()
        app.frame()
        root.update_idletasks()
        assert len(app.canvas.find_all())>200
        checks.append('start overlay and 3D scene created')
        app.key_down(SimpleNamespace(keysym='Return'))
        app.keys.add('w')
        for _ in range(60): app.update()
        assert abs(app.game.pos[2]-6)<1e-6
        app.keys.clear()
        app.keys.add('space')
        app.update()
        assert app.game.pos[1]>0
        checks.append('GUI input adapter moves and jumps using shared simulation')
        app.keys.clear()
        app.key_down(SimpleNamespace(keysym='p'))
        tick=app.game.tick
        app.update()
        assert app.game.tick==tick
        app.keys.clear()
        app.key_down(SimpleNamespace(keysym='p'))
        assert not app.paused
        checks.append('pause and resume freeze simulation')
        for state in ('won','lost'):
            app.game.state=state
            app.frame()
            assert any(('ĐẢO ĐÃ SÁNG' in app.canvas.itemcget(i,'text') or 'HẸN MÂY' in app.canvas.itemcget(i,'text')) for i in app.canvas.find_all() if app.canvas.type(i)=='text')
            app.restart()
            assert app.game.state=='playing' and app.game.tick==0 and app.game.score==0
        checks.append('both terminal overlays and restart reset game state')
        app.scene.draw(app.game,0,1152,760,started=True)
        start=time.perf_counter()
        for i in range(20):
            app.scene.draw(app.game,i,1152,760,started=True)
            root.update_idletasks()
        elapsed=time.perf_counter()-start
        target=ROOT/'docs/proof/phase-1'
        target.mkdir(parents=True,exist_ok=True)
        app.canvas.postscript(file=str(target/'desktop-canvas.ps'),colormode='color')
        (target/'gui-smoke.json').write_text(json.dumps(dict(checks=checks,canvas_items=len(app.canvas.find_all()),frames=20,wall_seconds=elapsed,render_fps=20/elapsed,limitations='Programmatic smoke on this Windows host; no manual interactive-play review or cross-platform runtime claim.'),indent=2)+'\n',encoding='utf-8')
        print('PASS: Tk desktop startup, movement, jump, pause, win/loss overlays, replay and Canvas export.')
    finally:
        root.destroy()


if __name__=='__main__': main()
