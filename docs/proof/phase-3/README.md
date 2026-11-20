# Bằng chứng Phase3 — Contract1.2

Tái tạo: `python3 tools/verify.py`; GUI/FPS: `python3 tools/gui_smoke.py`;
stress: `python3 tools/stress_renderer.py`. Output thật, không chỉnh log để đạt.
Source hash CRLF→LF, máy/timestamp trong verification.json. Timing tùy máy;
cùng mã/seed/scenario/input thì JSONL phải giống từng byte.

| Phạm vi | Bằng chứng | Kết quả |
|---|---|---|
| Regression58case +25fuel/drain/dawn/capacity/settings | [tests.txt](tests.txt) | 83test đạt |
| Decay/out/refuel/relight/full-nearest/capacity | fuel-out/refuel/relight/capacity.jsonl + unit tests | Đạt |
| Drain cộng dồn/60simtick/pause/pulse15/eject | drain-stack/drain-pause/drain-pulse/refuel-eject.jsonl | Đạt |
| Không earlywin/ngưỡng3/5,4/6,5/7/deathpriority | all-lit-running,dawn-won/lost-night1/2/3,dawn-expiry,dawn-relight + tests | Đạt |
| 11scenario v1.1 còn hiệu lực và17scenario mới | [verification.json](verification.json), inputs v11/v12 | 28case replay2lần byte-identical |
| Maintenance đến dawn không sửa state lúc chạy | [maintenance.json](maintenance.json), [inputs](maintenance.inputs.json), [output](maintenance.jsonl) | 7200step,3đèn,3lửa,580điểm |
| Full-night≤30s | benchmark-night1/2/3.jsonl, verification.json | Đủ14400/16200/18000step |
| Settings saved/palette/modelunchanged, fuel blink/HUD/shape | [gui-smoke.json](gui-smoke.json), [on](colorblind-low-on.png), [off](colorblind-low-off.png), [refill](refueled.png) | GUI smoke đạt |
| 30FPS1280×720 và all-lamps/shade-cap stress | gui-smoke.json, [renderer-stress.json](renderer-stress.json) | Xem số đo local theo từng Đêm |
| Fresh install/build/test/replay | [clean-check.txt](clean-check.txt) | Chạy ở thư mục tạm, không dùng cache dự án |
| Đa OS | GitHub Actions commit/tag phase3 | Xem run thực tế sau push |

Input nguồn ở tests/scenarios/v12/index.json và11case v11 không bị thay. ADR
và notes giải thích3fixture earlywin đã thay, không skipâmthầm. Gameplay120s
là **controlled maintenance challenge**, có scenario cho trước đèn/motes,
không tuyên bố là bản đồ mặc định. Code chỉ gửi move/interact, CLI phát lại khớp.

Ảnh được GUI tự lưu từ framebuffer thật; on/off cách nhau30bước mô phỏng,
có giấy tắt xẹp20%/rách. Cảnh warning dùng vector vì font có thể không có⚠.
Ảnh lit-night*.png và SVG là exports offscreen. GUI/audio là smoke tự động,
mixer dummy không chứng minh đã nghe thử trên loa; chưa có chơi/nghe/review
độc lập, video hoặc test ẩn. Không ghi những mục đó đã đạt.

Benchmark dùng invuln lớn/tắt gió để chạy trọn thời lượng; stress dùng scenario
đủ shade và mọi đèn100dầu. Giữ đúng số liệu chuẩn, không đổi luật để đạt FPS.
Source/data Phase1–2 giữ nguyên ở tag/thư mục cũ.

Replay maintenance:

```bash
python3 game.py --headless --seed 12 --night 1 --scenario tests/scenarios/v12/maintenance.json --inputs docs/proof/phase-3/maintenance.inputs.json --ticks 7200 --snapshot-every 120 --out replay.jsonl
```
