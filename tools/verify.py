"""Phase 2 evidence gate: behavioral tests, deterministic CLI scenarios, full nights."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
PROOF=ROOT/'docs/proof/phase-2'


def run(args,timeout=30):
    return subprocess.run([sys.executable]+args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)


def verify():
    PROOF.mkdir(parents=True,exist_ok=True)
    for name,args in [('build',['tools/build.py']),('tests',['-m','unittest','discover','-s','tests','-v']),('playthrough',['tools/playthrough.py'])]:
        p=run(args,timeout=180 if name=='build' else 30)
        (PROOF/(name+'.txt')).write_text(p.stdout+p.stderr,encoding='utf-8')
        if p.returncode: raise RuntimeError(name+' failed: '+p.stderr[-2000:])
    cases=json.loads((ROOT/'tests/scenarios/v11/index.json').read_text(encoding='utf-8'))
    results=[]
    for case in cases:
        name=case['name']; out=PROOF/(name+'.jsonl')
        args=['game.py','--headless','--seed','12','--night',str(case['night']),'--scenario','tests/scenarios/v11/'+name+'.json',
              '--inputs','tests/scenarios/v11/'+name+'.inputs.json','--ticks',str(case['ticks']),'--snapshot-every','1' if case['ticks']<=150 else '10','--out',str(out)]
        first=run(args)
        if first.returncode: raise RuntimeError(name+': '+first.stderr)
        data=out.read_bytes(); again=run(args)
        if again.returncode or out.read_bytes()!=data: raise RuntimeError('nondeterminism: '+name)
        records=[json.loads(line) for line in data.decode('utf-8').splitlines()]
        assert records[-1]['type']=='end'
        events=[e for e in records if e['type']=='event']
        snapshots=[e for e in records if e['type']=='snapshot']
        assert case['event'] in [e['name'] for e in events],name
        if name=='pause':
            frozen=[s for s in snapshots if s['state']=='paused']
            assert len(frozen)>1 and len({s['sim_tick'] for s in frozen})==1
        elif name=='fall': assert snapshots[-1]['player']['pos']==[0,0,0]
        elif name=='launch': assert snapshots[-1]['player']['pos'][0]>42 and snapshots[-1]['player']['grounded']
        elif name=='tiers': assert snapshots[-1]['player']['pos'][1]==6 and snapshots[-1]['player']['grounded']
        elif name=='wind': assert any(s['wind']['active'] for s in snapshots)
        elif name=='charm': assert len([e for e in events if e['name']=='dash'])>=2
        elif name.startswith('win-night'): assert records[-1]['state']=='won'
        results.append(dict(name=name,night=case['night'],sha256=hashlib.sha256(data).hexdigest(),deterministic=True,end=records[-1]))
    benchmarks=[]
    for night,expected in [(1,18000),(2,19800),(3,21600)]:
        out=PROOF/('benchmark-night%d.jsonl'%night)
        args=['game.py','--headless','--seed','12','--night',str(night),'--scenario','tests/scenarios/v11/benchmark%d.json'%night,
              '--ticks','21600','--snapshot-every','600','--out',str(out)]
        start=time.perf_counter(); result=run(args,timeout=30); elapsed=time.perf_counter()-start
        if result.returncode: raise RuntimeError(result.stderr)
        end=json.loads(out.read_text(encoding='utf-8').splitlines()[-1])
        assert end['ticks']==expected and end['state']=='lost' and elapsed<=30
        benchmarks.append(dict(night=night,steps=expected,wall_seconds=elapsed,steps_per_second=expected/elapsed,limit_seconds=30))
    source=[ROOT/'game.py',ROOT/'game.contract.json',ROOT/'requirements.txt']+sorted((ROOT/'src').rglob('*.py'))+sorted((ROOT/'tests').rglob('*.py'))+sorted((ROOT/'tools').glob('*.py'))
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in source}
    metadata=dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),contract_version='1.1',python=sys.version,platform=platform.platform(),processor=platform.processor(),logical_cpus=os.cpu_count(),
                  source_sha256=hashes,scenarios=results,benchmarks=benchmarks,
                  benchmark_fixture='Default standardized map/spawns/duration; long initial invulnerability and disabled wind prevent premature death/fall so full-night throughput is measured.',
                  limitations=['Hidden instructor tests unavailable','GUI/audio/palette/settings checks are recorded separately','Independent human play/listening review not performed'])
    (PROOF/'verification.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: v1.1 tests,14 deterministic feature scenarios, default-map bot replay and all3 full-night30s gates.')
    return 0


def main():
    global PROOF
    try:
        if '--check-only' in sys.argv:
            with tempfile.TemporaryDirectory(prefix='lantern-v11-gate-') as temp:
                PROOF=Path(temp); os.environ['LANTERN_PROOF_DIR']=temp
                return verify()
        os.environ['LANTERN_PROOF_DIR']=str(PROOF)
        return verify()
    except (RuntimeError,AssertionError,subprocess.TimeoutExpired) as error:
        print('VERIFICATION FAILED: '+str(error),file=sys.stderr)
        return 1


if __name__=='__main__': sys.exit(main())
