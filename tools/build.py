"""No downloads: validate the contract and compile Python source."""
import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
assert contract["contract_version"] == "1.0"
assert contract["tuning"]["lantern_count_night1"] == 5
sources = [ROOT / "game.py"] + list((ROOT / "src").rglob("*.py"))
for source in sources:
    py_compile.compile(str(source), doraise=True)
print("Build OK: %d Python modules; no third-party dependencies." % len(sources))
