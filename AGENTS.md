# Đảo Đèn Lồng — working instructions

- Read `docs/requirements/phase-1.md` before implementation. PRD-0 and Contract
  v1.0 were supplied by the user. Tickets 02–04 are still missing.
- Python 3.9+; pure simulation in `src/lantern_island/model.py`, GUI in `view.py`.
- Run: `python game.py`. Tests: `python -m unittest discover -s tests -v`.
- Evidence gate: `python tools/verify.py`; it must exit nonzero on any failed test.
- Preserve the six original lab documents and all harness files.
- Headless: `python game.py --headless --seed 12 --night 1 --ticks 600 --out run.jsonl`.
- Manifest tuning is the runtime source of truth. Use XZ and inclusive radii.
- Tick 0 is setup; input k produces events/state k+1. Buttons use rising edges.
- Setup has no events/score. Validate even input frames beyond --ticks.
- Keep deterministic fixed steps, stable entity IDs, and finite validated inputs.
- Save evidence from execution only; never edit generated output to make it pass.
- GUI smoke: `python tools/gui_smoke.py`; render export: `python tools/export_scene.py`.
- Render tests do not replace manual play or independent review; report honestly.
- Do not create phase tags or a final release before the corresponding ticket is
  implemented and verified. Never fabricate historical deadlines or token metrics.
