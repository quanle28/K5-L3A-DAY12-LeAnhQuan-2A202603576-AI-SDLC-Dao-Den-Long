"""One-command evidence gate. A failed check always fails the process."""
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import time
import tempfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
PROOF=ROOT/"docs/proof/phase-1"


def run(args):
    result=subprocess.run([sys.executable]+args,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace")
    return result


def verify():
    PROOF.mkdir(parents=True,exist_ok=True)
    build=run(["tools/build.py"])
    test=run(["-m","unittest","discover","-s","tests","-v"])
    (PROOF/"tests.txt").write_text(build.stdout+build.stderr+test.stdout+test.stderr,encoding="utf-8")
    if build.returncode or test.returncode:
        print("FAILED. See docs/proof/phase-1/tests.txt")
        return 1
    playthrough=run(["tools/playthrough.py"])
    (PROOF/"playthrough.txt").write_text(playthrough.stdout+playthrough.stderr,encoding="utf-8")
    if playthrough.returncode:
        print("FAILED: full default map playthrough")
        return 1
    results=[]
    for name,ticks,expected in [("pickup-deposit",130,"playing"),("pulse",200,"playing"),("win",120,"won"),("loss",120,"lost"),("dawn",120,"lost")]:
        target=PROOF/(name+".jsonl")
        args=["game.py","--headless","--seed","12","--night","1","--scenario","tests/scenarios/"+name+".json","--ticks",str(ticks),"--out",str(target)]
        inputs=ROOT/"tests/scenarios"/(name+".inputs.json")
        if inputs.exists(): args.extend(["--inputs",str(inputs)])
        first=run(args)
        if first.returncode: raise RuntimeError(first.stderr)
        content=target.read_bytes()
        second=run(args)
        if second.returncode or target.read_bytes()!=content: raise RuntimeError("nondeterministic: "+name)
        rows=[json.loads(line) for line in content.decode().splitlines()]
        assert rows[-1]["state"]==expected,(name,rows[-1])
        names=[r.get("name") for r in rows]
        if name=="pickup-deposit":
            assert names.count("mote_picked")==10 and "lantern_lit" in names
        if name=="pulse": assert "pulse" in names
        results.append(dict(scenario=name,sha256=hashlib.sha256(content).hexdigest(),deterministic=True,end=rows[-1]))
    start=time.perf_counter()
    benchmark=run(["game.py","--headless","--seed","12","--night","1","--scenario","tests/scenarios/benchmark.json","--ticks","18000","--snapshot-every","600","--out",str(PROOF/"benchmark.jsonl")])
    if benchmark.returncode: raise RuntimeError(benchmark.stderr)
    elapsed=time.perf_counter()-start
    benchmark_end=json.loads((PROOF/"benchmark.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert benchmark_end["ticks"]==18000
    source_files=[ROOT/"game.py",ROOT/"game.contract.json"]+sorted((ROOT/"src").rglob("*.py"))+sorted((ROOT/"tests").rglob("*.py"))+sorted((ROOT/"tools").glob("*.py"))
    source_hashes={str(path.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for path in source_files}
    metadata=dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),source_sha256=source_hashes,python=sys.version,platform=platform.platform(),processor=platform.processor(),logical_cpus=os.cpu_count(),
                  results=results,benchmark=dict(wall_seconds=elapsed,steps=18000,steps_per_second=18000/elapsed,note="Includes interpreter startup and JSONL I/O; central safe lamp, procedural spawns enabled. Not a rendering FPS measurement."),
                  limitations=["No hidden instructor tests available", "macOS/Linux runtime requires CI or another machine", "Visual manual review and independent review must be recorded separately"])
    (PROOF/"verification.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS: tests, five scenario replays, deterministic JSONL and evidence saved.")
    return 0


def main():
    global PROOF
    if '--check-only' in sys.argv:
        with tempfile.TemporaryDirectory(prefix='lantern-gate-') as temp:
            PROOF=Path(temp)
            os.environ['LANTERN_PROOF_DIR']=temp
            return verify()
    return verify()


if __name__=="__main__": sys.exit(main())
