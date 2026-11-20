# Đảo Đèn Lồng — working instructions

- Read `docs/requirements/phase-4.md` and ADR0003. Complete Ticket-04/v1.3
  was supplied in chat. Keep every v1.2 gameplay rule unchanged.
- Python 3.9+; pure simulation in `model.py`, geometry in `maps.py`, Pygame GUI in
  `view.py`/`render.py`. `python tools/build.py` installs pinned runtime into .runtime.
- Run: `python game.py`. Tests: `python -m unittest discover -s tests -v`.
- Evidence gate: `python tools/verify.py`; it must exit nonzero on any failed test.
- Preserve the six original lab documents and all harness files.
- Headless: `python game.py --headless --seed 12 --night 1 --ticks 600 --out run.jsonl`.
- Manifest tuning is the runtime source of truth. Use XZ and inclusive radii.
- Tick 0 is setup; input k produces events/state k+1. Buttons use rising edges.
- Follow Ticket-02's 12-step order. Pause increments wall tick, never sim_tick/counters.
- Score motes on DEPOSIT/refuel, not pickup. No early win. At dawn only:
  no_flames > alive and lit>=ceil(win_ratio*count) wins dawn_survived > dawn loss.
- Fuel uses integer 1/60 units; step2 decay/drain/out precede interactions.
- Only lit fuel>=30 creates safe. Pulse on drain gives TOTAL15, not20.
- XZ pickup/hit include the required height gate; pulse uses actual 3D foot+.8 center.
- Setup has no events/score. Validate even input frames beyond --ticks.
- Keep deterministic fixed steps, stable entity IDs, and finite validated inputs.
- Save evidence from execution only; never edit generated output to make it pass.
- GUI smoke: `python tools/gui_smoke.py`; render export: `python tools/export_scene.py`.
- GUI gate is >=30 FPS at 1280x720 for every night. Full-night headless <=30 seconds.
- Audio smoke uses dummy mixer; do not describe it as a human listening test.
- Render tests do not replace manual play or independent review; report honestly.
- Preserve phase-1/2/3 tags and proof. Phase4 output goes to docs/proof/phase-4.
- Benchmark: exact200wander/100motes/3lit100, orbitR30Y15/15s, warm3s;
  disable spawn/damage/pickup/fuel/end. Shared renderer, no hidden quality downgrade.
- Benchmark/soak numbers must be actual. Save raw dt and RSS method. Report local
  thresholds separately from instructor hardware; do not fabricate a pass.
- Leaderboard/settings data are local user data, never commit them. Tests use temp dirs.
- Demo must show live GUI/real command output; disclose automated input, never call it human play.
- Do not create phase tags or a final release before the corresponding ticket is
  implemented and verified. Never fabricate historical deadlines or token metrics.
