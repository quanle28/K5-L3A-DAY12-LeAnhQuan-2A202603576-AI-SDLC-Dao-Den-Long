"""Build a standalone onedir executable and smoke-test it before zipping."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import venv

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--install',action='store_true'); args=parser.parse_args()
    build_env=ROOT/'.buildenv'
    python=build_env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if args.install:
        venv.EnvBuilder(with_pip=True).create(build_env)
        subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(ROOT/'requirements.txt'),'PyInstaller==6.11.1','setuptools==75.6.0','pyinstaller-hooks-contrib==2024.11'],check=True)
    if not python.exists(): raise SystemExit('Run tools/package_release.py --install first')
    env=dict(os.environ)
    env.pop('PYTHONPATH',None); env['PYTHONNOUSERSITE']='1'
    subprocess.run([str(python),'-I','-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','DaoDenLong',
                    '--paths',str(ROOT/'.runtime'),'--add-data',str(ROOT/'game.contract.json')+os.pathsep+'.',
                    '--exclude-module','numpy','--exclude-module','tkinter','--exclude-module','PIL','--exclude-module','matplotlib',
                    # pygame.pkgdata explicitly supports files next to __file__ when pkg_resources
                    # is absent. The pygame hook includes those data; no build-time setuptools
                    # or vendored jaraco/backports should be shipped in this game runtime.
                    '--exclude-module','pkg_resources','--exclude-module','setuptools',str(ROOT/'game.py')],cwd=ROOT,env=env,check=True)
    folder=ROOT/'dist/DaoDenLong'; exe=folder/('DaoDenLong.exe' if os.name=='nt' else 'DaoDenLong')
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)/'run.jsonl'
        subprocess.run([str(exe),'--headless','--seed','12','--night','3','--ticks','60','--out',str(out)],check=True,timeout=30)
        records=[json.loads(line) for line in out.read_text().splitlines()]
        assert records[0]['tick']==0 and records[-1]['ticks']==60 and records[-1]['type']=='end'
        subprocess.run([str(exe),'--data-dir',temp,'--export-leaderboard',str(Path(temp)/'scores.json')],check=True,timeout=30)
        assert json.loads((Path(temp)/'scores.json').read_text())=={'entries':[]}
        subprocess.run([str(exe),'--soak','--seed','7','--nights','3','--out',str(Path(temp)/'soak.json')],check=True,timeout=30)
    for file in ('README.md','CREDITS.md','LICENSE','CHANGELOG.md'):
        shutil.copy2(ROOT/file,folder/file)
    # Preserve upstream runtime notices for the standalone redistribution.
    notices=folder/'THIRD-PARTY'; notices.mkdir(exist_ok=True)
    for pattern in ('pygame-*.dist-info','psutil-*.dist-info'):
        for directory in (ROOT/'.runtime').glob(pattern): shutil.copytree(directory,notices/directory.name,dirs_exist_ok=True)
    shutil.copytree(ROOT/'docs/licenses',notices/'licenses',dirs_exist_ok=True)
    python_license=build_env/('LICENSE.txt' if os.name=='nt' else 'lib/python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'/LICENSE.txt')
    if not python_license.exists(): python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.exists(): shutil.copy2(python_license,notices/'PYTHON-LICENSE.txt')
    label={'Windows':'windows','Linux':'linux','Darwin':'macos'}[platform.system()]+'-'+platform.machine().lower()
    metadata=dict(platform=platform.platform(),python=sys.version,headless_export_soak_smoke=True,
                  source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
                                 for p in [ROOT/'game.py',ROOT/'game.contract.json']+sorted((ROOT/'src').rglob('*.py'))})
    (folder/'package.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    archive=shutil.make_archive(str(ROOT/'dist'/('DaoDenLong-v1.0.0-'+label)),'zip',ROOT/'dist','DaoDenLong')
    metadata.update(archive=Path(archive).name,sha256=hashlib.sha256(Path(archive).read_bytes()).hexdigest(),bytes=Path(archive).stat().st_size)
    proof=ROOT/'docs/proof/phase-4'; proof.mkdir(parents=True,exist_ok=True)
    (proof/('package-'+label+'.json')).write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print('PACKAGED AND SMOKE-TESTED: '+archive)

if __name__=='__main__': main()
