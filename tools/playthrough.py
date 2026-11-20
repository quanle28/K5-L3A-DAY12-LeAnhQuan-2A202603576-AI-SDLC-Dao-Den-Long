"""Play the untouched default map using only legal contract inputs, then replay CLI."""
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.lantern_island.model import DEFAULT_INPUT, Game, distance, validate_inputs


def main():
    # Seed 1 is a normal default map; the bot must obey the same player inputs.
    game=Game(1)
    frames=[]
    previous_pulse=previous_dash=False
    for tick in range(18000):
        if game.state!='playing': break
        unlit=[l for l in game.lanterns if not l['lit']]
        shades=[s for s in game.shades if s['state'] in ('wander','chase') and not s['eject']]
        danger=min([distance(game.pos,s['pos']) for s in shades]+[100])
        def cost(p): return distance(game.pos,p)+sum(max(0,7-distance(p,s['pos']))*4 for s in shades)
        if game.carried>=10 or not game.motes:
            target=min(unlit,key=lambda l:cost(l['pos']))['pos']
        else: target=min(game.motes,key=lambda m:cost(m['pos']))['pos']
        dx,dz=target[0]-game.pos[0],target[2]-game.pos[2]
        d=math.hypot(dx,dz)
        angle=math.atan2(dz,dx); best=None
        for offset in (0,.35,-.35,.7,-.7,1.2,-1.2,1.8,-1.8,math.pi):
            x,z=math.cos(angle+offset),math.sin(angle+offset)
            future=[game.pos[0]+x*3,0,game.pos[2]+z*3]
            if math.hypot(future[0],future[2])>39: continue
            clearance=min([distance(future,s['pos']) for s in shades]+[30])
            value=math.cos(offset)*2+min(6,clearance)*.7-max(0,3.5-clearance)*4
            if best is None or value>best[0]: best=(value,x,z)
        move=[best[1],best[2]] if d>.15 and best else [0,0]
        pulse=danger<3.5 and game.carried>=3 and not game.pulse_cd_ticks and not previous_pulse
        dash=not game.dash_cd_ticks and not game.dash_ticks and not previous_dash and d>4
        controls=dict(DEFAULT_INPUT,move=move,pulse=pulse,dash=dash,interact=tick%2==0)
        frames.append(dict(tick=tick,move=move,interact=controls['interact'],pulse=pulse,dash=dash))
        game.step(controls)
        previous_pulse,previous_dash=pulse,dash
    assert game.state=='won',game.snapshot()
    target=Path(os.environ.get('LANTERN_PROOF_DIR',str(ROOT/'docs/proof/phase-2')))
    target.mkdir(parents=True,exist_ok=True)
    inputs=target/'full-play.inputs.json'
    data={'frames':frames}
    validate_inputs(data)
    inputs.write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8')
    out=target/'full-play.jsonl'
    args=[sys.executable,str(ROOT/'game.py'),'--headless','--seed','1','--night','1','--inputs',str(inputs),'--ticks','18000','--snapshot-every','120','--out',str(out)]
    subprocess.run(args,cwd=ROOT,check=True)
    result=json.loads(out.read_text(encoding='utf-8').splitlines()[-1])
    assert result==dict(type='end',ticks=game.tick,state=game.state,score=game.score)
    summary=dict(seed=1,scenario='default, no overrides',end=result,flames=game.flames,lit=sum(l['lit'] for l in game.lanterns),
                 method='Bot observes positions and sends move/interact/dash/pulse only; no teleport, resource injection, or modified rules. CLI replay must reach the same result.',limitations='Automated gameplay proof, not a recording of human play. Phase 1 greedy bot lost under new rules; steering and seed 1 are used here.')
    (target/'full-play.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('PASS: default Night 1 won through contract inputs, CLI replay matched (%d ticks, %d points).'%(game.tick,game.score))


if __name__=='__main__': main()
