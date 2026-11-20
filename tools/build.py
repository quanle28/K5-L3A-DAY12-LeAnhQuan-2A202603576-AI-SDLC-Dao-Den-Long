"""Install the pinned desktop runtime locally and compile all Python sources."""
import json
import py_compile
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
assert contract["contract_version"] == "1.2"
assert contract["tuning"]["lantern_count_night1"] == 5
sources = [ROOT / "game.py"] + list((ROOT / "src").rglob("*.py"))
for source in sources:
    py_compile.compile(str(source), doraise=True)
sys.path.insert(0,str(ROOT/'.runtime'))
if importlib.util.find_spec('pygame') is None:
    subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--target',str(ROOT/'.runtime'),'-r',str(ROOT/'requirements.txt')],check=True)
print("Build OK: %d Python modules; pinned Pygame desktop runtime ready. Headless uses only stdlib." % len(sources))
if '--run' in sys.argv:
    raise SystemExit(subprocess.call([sys.executable,str(ROOT/'game.py')],cwd=ROOT))
