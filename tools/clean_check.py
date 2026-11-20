"""Verify the distributable sources in a fresh directory without local caches."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    logs=[]
    with tempfile.TemporaryDirectory(prefix='lantern-clean-') as temp:
        clean=Path(temp)/'game'
        clean.mkdir()
        for name in ('game.py','game.contract.json','requirements.txt'):
            shutil.copy2(ROOT/name,clean/name)
        for name in ('src','tests','tools'):
            shutil.copytree(ROOT/name,clean/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for args in (['tools/build.py'],['-m','unittest','discover','-s','tests','-v'],['tools/playthrough.py']):
            result=subprocess.run([sys.executable]+args,cwd=clean,capture_output=True,text=True,encoding='utf-8',errors='replace')
            logs.append('$ python '+' '.join(args)+'\n'+result.stdout+result.stderr)
            if result.returncode:
                print(logs[-1])
                return 1
    target=ROOT/'docs/proof/phase-2/clean-check.txt'
    target.write_text('\n'.join(logs),encoding='utf-8')
    print('PASS: fresh directory dependency install, build, tests and standard-map CLI playthrough without .git, .qa or project caches.')
    return 0


if __name__=='__main__': sys.exit(main())
