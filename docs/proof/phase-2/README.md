# Bằng chứng Phase 2 — Contract v1.1

Tái tạo logic: `python3 tools/verify.py`; GUI/FPS: `python3 tools/gui_smoke.py`;
stress: `python3 tools/stress_renderer.py`. Tất cả output do chương trình chạy
thật sinh ra. Không sửa log/JSONL để đổi kết quả. Source SHA-256 và môi trường
ở verification.json; hash chuẩn hóa CRLF→LF. Timestamp/timing tùy máy, replay
JSONL phải giống từng byte với cùng seed/input/scenario/mã.

| Phạm vi nghiệm thu | Bằng chứng | Kết quả local |
|---|---|---|
| Chuẩn hóa, input, physics, điểm, hit/recoil/fall/respawn, safe/pulse, timers | [tests.txt](tests.txt) | 58test đạt |
| Deposit/dash/pulse/fall/pause | Các JSONL cùng tên và input tại tests/scenarios/v11 | Đạt, mỗi case replay2lần |
| Gió Lạc steal/drop/priority, Bùa speed/dash/respawn/TTL | [steal](drifter-steal.jsonl), [drop](drifter-drop.jsonl), [charm](charm.jsonl), unit tests | Đạt |
| Đảo Cau/bục, Đảo Chuông/tầng/ramp/tower/gió | [launch](launch.jsonl), [tiers](tiers.jsonl), [wind](wind.jsonl), map tests | Đạt |
| Kết thúc mỗi Đêm | win-night1/2/3.jsonl | Đạt với đèn dựng sẵn (không cộng điểm setup) |
| Lượt chơi defaultNight1 không override | [full-play](full-play.json), [inputs](full-play.inputs.json), [output](full-play.jsonl) | Seed1 thắng5/5,11107tick,1403điểm,3lửa |
| Tất định và fullnight≤30s | [verification.json](verification.json), benchmark-night1/2/3.jsonl | 14 replay byte-identical; chạy đủ18000/19800/21600step |
| Menu→intro→3đêm→result→BìnhMinh, loss/retry, won-only total, settings/pause/mouse | [gui-smoke.json](gui-smoke.json), [menu](menu.png), [dawn](dawn.png) | Programmatic GUI smoke đạt |
| Audio nhạc/SFX và countdown | gui-smoke.json, audio.py PCM | Mixer dummy/routing đạt; chưa nghe thử trên thiết bị thực |
| HUD/nearE/timerred/arrow, ambient endpoints | gui-smoke.json, [hud-danger.png](hud-danger.png) | Đạt |
| 30FPS1280×720 cả3Đêm | gui-smoke.json, night1/2/3.png | Đạt local; có logic/draw/flip/eventpump trong phép đo |
| Stress đủ6/8/10shade,2drifter,24/30mote | [renderer-stress.json](renderer-stress.json) | ≥30FPS local |
| Màu và sáng dần | [palette.png](palette.png), lit-night1/2/3.png, palette tests | Vật liệu chuẩn, ambient.15→.70 |
| Cài/build/test/replay bản sao sạch | [clean-check.txt](clean-check.txt) | Đạt, không dùng.runtime/.qa của dự án gốc |
| Đa OS | Workflow Phase2, kết quả GitHub Actions của commit/tag | Xem run thật sau push |

Fixture chuẩn tại `tests/scenarios/v11/index.json`. Benchmark dùng thời lượng/
bản đồ/spawn chuẩn, invuln lớn và tắt gió để không kết thúc sớm vì chết/rơi;
case wind/rơi riêng vẫn được kiểm tra. Stress cũng dùng override hợp lệ để
đo cap population; không thay luật game. Các phép đo ghi số frame/độ phân
giải/thời gian, không giả là đo trên máy chấm của giảng viên.

`night*.png`, menu/dawn/hud-danger là framebuffers thật do GUI smoke lưu.
`lit-night*.png`, palette và SVG là offscreen exports, không gọi là clip chơi tay.
Flow kết thúc3Đêm dùng scenario để test màn hình; chỉ full-playNight1 là bot
chơi màn gốc từ đầu bằng input thường. Chưa có test ẩn, người nghe/thử độc lập
hoặc video demo. Không nhận những mục đó đã đạt.

Phát lại bot thắng:

```bash
python3 game.py --headless --seed 1 --night 1 --inputs docs/proof/phase-2/full-play.inputs.json --ticks 18000 --snapshot-every 120 --out replay.jsonl
```

Bằng chứng Phase1 ở thư mục/tag riêng, giữ nguyên. Ticket03/04 chưa có.
