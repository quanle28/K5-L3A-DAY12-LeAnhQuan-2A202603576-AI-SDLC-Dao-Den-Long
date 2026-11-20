"""Install the pinned desktop runtime locally and compile all Python sources."""
import json
import py_compile
import importlib.util
import importlib.metadata
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
assert contract["contract_version"] == "1.3"
assert contract["tuning"]["lantern_count_night1"] == 5
sources = [ROOT / "game.py"] + list((ROOT / "src").rglob("*.py"))
for source in sources:
    py_compile.compile(str(source), doraise=True)
sys.path.insert(0,str(ROOT/'.runtime'))
pins={'pygame':'2.6.1','psutil':'6.1.1'}
def matching(name,version):
    try: return importlib.metadata.version(name)==version
    except importlib.metadata.PackageNotFoundError: return False
if any(not matching(name,version) for name,version in pins.items()):
    subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--upgrade','--target',str(ROOT/'.runtime'),'-r',str(ROOT/'requirements.txt')],check=True)
print("Build OK: %d Python modules; pinned Pygame desktop runtime ready. Headless uses only stdlib." % len(sources))
if '--run' in sys.argv:
    raise SystemExit(subprocess.call([sys.executable,str(ROOT/'game.py')],cwd=ROOT))
