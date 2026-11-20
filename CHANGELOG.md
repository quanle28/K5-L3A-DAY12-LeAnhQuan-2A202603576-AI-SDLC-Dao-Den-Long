# Changelog

## v1.0.0 / phase-4 — Bình minh / Contract v1.3

- Thêm benchmark chuẩn và raw frame times; soak10Đêm cùng tiến trình, RSS thật.
- Bảng xếp hạng top10 bền vững, tên Unicode, export CLI, chỉ cộng Đêm thắng.
- Đổi9phím/báo trùng/khôi phục, phụ đề+edgearrow, giảm chuyển động, chữ18px/lớn1.25.
- Tối ưu clip viewport và LOD dùng chung game/bench; giữ nguyên28đầu ra CLI Phase3.
- 96test, GUI/clean/build gates, video live-framebuffer72s, retro4phase,
  standalone Windows/Linux/macOS và workflow GitHub Release.
- Không thay luật gameplay1.2. Manifest1.3 thêm bench_cmd/soak_cmd.
- Bỏ shortcut R chơi lại để phím đó có thể được gán tự do; chơi lại trong pause/result.

## phase-3 — Đèn cạn dầu / Contract v1.2 — breaking changes

- Đèn sáng không còn vĩnh viễn:100dầu, hao1/s, có refuel/out/ever_lit/relit_count;
  firstcost10,relight5. Safe chỉ khi fuel≥30. Wander/drain AI hút5/s cộng dồn.
- **Bỏ early-win/all_lit**. Đêm240/270/300s, chỉ thắng dawn_survived khi còn
  sống và đủceil60%đèn; no_flames ưu tiên trước ở tick cuối.
- Capacity10+2mỗi lần thắp, cap20. **Thay toàn bộ điểm**:5/mote,100first,
  40relight,5pulse/15drainpulse, dawn50+floorfuel/lamp+50/flame, bỏ timebonus.
- Contract1.2 thêm fuel/ever_lit/relit_count/capacity/drain/target và events;
  lantern_lit thêm relight. Scenario mới, điểm/setup/history được phân biệt.
- Colorblind lưu bền, warning trắng+vector⚠, shade viền/mắt xanh, giấy rách/xẹp,
  fuelbar nhấp nháy1Hz. Tối ưu convex floor/disc, không đổi collision/tuning.
- ADR0003,83test,28scenario replay, controlledmaintenance và GUI/FPS/clean gates.
  Giữ nguyên tag/proof1–2; chưa làm Ticket04.

## phase-2 — Ba hòn đảo / Contract v1.1

- Chuẩn hóa toàn bộ tuning, score khi nạp, tick order, XZ/height/3D pulse,
  shade states, safe ejection, dropped TTL, rơi và hồi sinh.
- Ba bản đồ chuẩn, ramp/tower/bridge/pads/wind; dash, Gió Lạc và Bùa Gió.
- Campaign/intro/results/BìnhMinh, pause/options, settings lưu bền, nhạc/SFX gốc,
  HUD/palette/ambient; chuyển frontend sang Pygame để đạt30FPS1280×720.
- 58test,14scenario deterministic, fullnight30s gate, GUI/FPS/stress/clean install.
- Giữ nguyên tag và proof phase1; chưa triển khai Ticket03/04.

## phase-1 — PRD-0 / Contract v1.0

- Một màn 3D Đêm 1 – Đảo Bến: Mây, năm đèn, đom đóm, Bóng Mực đuổi,
  nhảy, pulse, vùng sáng, điểm, bình minh, thắng/thua và chơi lại.
- Manifest là nguồn tuning duy nhất; headless 60Hz, scenario/input chuẩn,
  JSONL snapshot/event/end, validation và deterministic replay.
- Kiểm chứng tự động, lượt chơi màn gốc, Tk smoke, bản xuất renderer,
  benchmark/thư mục sạch, AGENTS, hook và CI đa nền tảng.
- Phase 2–4 chưa triển khai, chờ ticket thực tế.
