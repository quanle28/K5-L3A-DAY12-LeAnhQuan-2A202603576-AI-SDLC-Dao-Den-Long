"""Play the untouched default map using only legal contract inputs, then replay CLI."""
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.lantern_island.model import DEFAULT_INPUT, Game, distance, validate_inputs


def main():
    game=Game(12)
    frames=[]
    for tick in range(18000):
        if game.state!='playing': break
        unlit=[l for l in game.lanterns if not l['lit']]
        if game.carried>=10:
            target=min(unlit,key=lambda l:distance(game.pos,l['pos']))['pos']
        else:
            target=min(game.motes,key=lambda m:distance(game.pos,m['pos']))['pos'] if game.motes else [0,0,0]
        dx,dz=target[0]-game.pos[0],target[2]-game.pos[2]
        d=math.hypot(dx,dz)
        move=[dx/d if d>.2 else 0,dz/d if d>.2 else 0]
        controls=dict(DEFAULT_INPUT,move=move,interact=tick%2==0)
        frames.append(dict(tick=tick,move=move,interact=controls['interact']))
        game.step(controls)
    assert game.state=='won',game.snapshot()
    target=ROOT/'docs/proof/phase-1'
    target.mkdir(parents=True,exist_ok=True)
    inputs=target/'full-play.inputs.json'
    data={'frames':frames}
    validate_inputs(data)
    inputs.write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8')
    out=target/'full-play.jsonl'
    args=[sys.executable,str(ROOT/'game.py'),'--headless','--seed','12','--night','1','--inputs',str(inputs),'--ticks','18000','--snapshot-every','120','--out',str(out)]
    subprocess.run(args,cwd=ROOT,check=True)
    result=json.loads(out.read_text(encoding='utf-8').splitlines()[-1])
    assert result==dict(type='end',ticks=game.tick,state=game.state,score=game.score)
    summary=dict(seed=12,scenario='default, no overrides',end=result,flames=game.flames,lit=sum(l['lit'] for l in game.lanterns),
                 method='Bot observes positions and sends move/interact only; no teleport, resource injection, or modified rules. CLI replay must reach the same result.',limitations='Automated gameplay proof, not a recording of human play.')
    (target/'full-play.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('PASS: default Night 1 won through contract inputs, CLI replay matched (%d ticks, %d points).'%(game.tick,game.score))


if __name__=='__main__': main()
