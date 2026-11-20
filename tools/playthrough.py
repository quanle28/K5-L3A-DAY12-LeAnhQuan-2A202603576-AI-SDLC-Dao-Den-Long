"""Play and CLI-replay a declared controlled v1.2 maintenance challenge."""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.lantern_island.model import Game,DEFAULT_INPUT,distance,validate_inputs


def main():
    scenario=ROOT/'tests/scenarios/v12/maintenance.json'
    game=Game(12,json.loads(scenario.read_text(encoding='utf-8')))
    frames=[]
    for tick in range(7200):
        if game.state in ('won','lost'): break
        lamps=game.lanterns[:3]
        weakest=min(lamps,key=lambda l:(l['fuel_units'],l['id']))
        needy=not weakest['lit'] or weakest['fuel_units']<75*60
        if game.carried and needy: target=weakest['pos']
        elif game.carried<game.capacity and game.motes:
            target=min(game.motes,key=lambda m:distance(game.pos,m['pos']))['pos']
        else: target=game.pos
        dx,dz=target[0]-game.pos[0],target[2]-game.pos[2]; d=math.hypot(dx,dz)
        move=[dx/d,dz/d] if d>.15 else [0,0]
        interact=bool(game.carried and needy and distance(game.pos,weakest['pos'])<=2 and tick%2==0)
        c=dict(DEFAULT_INPUT,move=move,interact=interact)
        frames.append(dict(tick=tick,move=move,interact=interact)); game.step(c)
    assert game.state=='won',game.snapshot()
    assert game.sim_tick==7200 and sum(l['lit'] for l in game.lanterns)>=3
    target=Path(os.environ.get('LANTERN_PROOF_DIR',str(ROOT/'docs/proof/phase-3'))); target.mkdir(parents=True,exist_ok=True)
    data={'frames':frames}; validate_inputs(data)
    inp=target/'maintenance.inputs.json'; inp.write_text(json.dumps(data,separators=(',',':'))+'\n',encoding='utf-8')
    out=target/'maintenance.jsonl'
    subprocess.run([sys.executable,str(ROOT/'game.py'),'--headless','--seed','12','--night','1','--scenario',str(scenario),'--inputs',str(inp),'--ticks','7200','--snapshot-every','120','--out',str(out)],cwd=ROOT,check=True)
    records=[json.loads(line) for line in out.read_text(encoding='utf-8').splitlines()]
    assert records[-1]==dict(type='end',ticks=game.tick,state=game.state,score=game.score)
    assert any(r.get('name')=='refuel' for r in records)
    summary=dict(seed=12,scenario='tests/scenarios/v12/maintenance.json',end=records[-1],flames=game.flames,
                 lit=sum(l['lit'] for l in game.lanterns),method='Controlled120s maintenance challenge with declared prelit lamps/motes. Bot sends legal move/interact only; no runtime mutations. CLI replay matches.',
                 limitations='Not an untouched default-map playthrough or human play recording; Phase2 early-win bot is superseded by the dawn objective.')
    (target/'maintenance.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('PASS: controlled maintenance survives all7200steps to dawn; CLI replay matched (%dpoints).'%game.score)


if __name__=='__main__': main()
