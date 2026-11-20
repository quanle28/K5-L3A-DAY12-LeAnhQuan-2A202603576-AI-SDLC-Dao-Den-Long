"""Compare actual CLI bytes against the immutable phase-3 tag, not golden guesses."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    report=[]
    with tempfile.TemporaryDirectory(prefix='lantern-regression-') as temp:
        temp=Path(temp); archive=temp/'old.tar'; old=temp/'old'; old.mkdir()
        subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'archive','phase-3','-o',str(archive)],cwd=ROOT,check=True)
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                target=(old/member.name).resolve()
                if old.resolve() not in target.parents or member.issym() or member.islnk(): raise ValueError('unsafe archive')
            tar.extractall(old)
        cases=[]
        for folder in ('v11','v12'):
            for case in json.loads((ROOT/'tests/scenarios'/folder/'index.json').read_text(encoding='utf-8')):
                if not case['name'].startswith('win-night'): cases.append((folder,case))
        for folder,c in cases:
            stem='tests/scenarios/'+folder+'/'+c['name']; outputs=[]
            for i,work in enumerate((old,ROOT)):
                out=temp/('result%d.jsonl'%i)
                subprocess.run([sys.executable,'game.py','--headless','--seed','12','--night',str(c['night']),
                                '--scenario',stem+'.json','--inputs',stem+'.inputs.json','--ticks',str(c['ticks']),
                                '--snapshot-every','1','--out',str(out)],cwd=work,check=True,timeout=30)
                outputs.append(out.read_bytes())
            assert outputs[0]==outputs[1],c['name']+' changed headless output'
            report.append(dict(name=c['name'],identical=True,sha256=hashlib.sha256(outputs[1]).hexdigest()))
    path=ROOT/'docs/proof/phase-4/phase3-regression.json'; path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(baseline_tag='phase-3',cases=report),indent=2)+'\n')
    print('PASS: %d headless CLI outputs byte-identical to phase-3.'%len(report))

if __name__=='__main__': main()
