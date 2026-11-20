# Đảo Đèn Lồng — working instructions

- Read `docs/requirements/phase-2.md` and `phase-2-standard.md`. Complete Ticket-02
  and Contract v1.1 were supplied in chat. Tickets 03–04 are not supplied.
- Python 3.9+; pure simulation in `model.py`, geometry in `maps.py`, Pygame GUI in
  `view.py`/`render.py`. `python tools/build.py` installs pinned runtime into .runtime.
- Run: `python game.py`. Tests: `python -m unittest discover -s tests -v`.
- Evidence gate: `python tools/verify.py`; it must exit nonzero on any failed test.
- Preserve the six original lab documents and all harness files.
- Headless: `python game.py --headless --seed 12 --night 1 --ticks 600 --out run.jsonl`.
- Manifest tuning is the runtime source of truth. Use XZ and inclusive radii.
- Tick 0 is setup; input k produces events/state k+1. Buttons use rising edges.
- Follow Ticket-02's 12-step order. Pause increments wall tick, never sim_tick/counters.
- Score motes on DEPOSIT, not pickup. Terminal priority: no_flames > all_lit > dawn.
- XZ pickup/hit include the required height gate; pulse uses actual 3D foot+.8 center.
- Setup has no events/score. Validate even input frames beyond --ticks.
- Keep deterministic fixed steps, stable entity IDs, and finite validated inputs.
- Save evidence from execution only; never edit generated output to make it pass.
- GUI smoke: `python tools/gui_smoke.py`; render export: `python tools/export_scene.py`.
- GUI gate is >=30 FPS at 1280x720 for every night. Full-night headless <=30 seconds.
- Audio smoke uses dummy mixer; do not describe it as a human listening test.
- Render tests do not replace manual play or independent review; report honestly.
- Phase 2: use standardized numbers. Preserve phase-1 tag/proof. Store
  preparation and later Phase 2 evidence in docs/proof/phase-2, never over phase-1.
- Do not create phase tags or a final release before the corresponding ticket is
  implemented and verified. Never fabricate historical deadlines or token metrics.
