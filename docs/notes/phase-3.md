# Phase3 — evaluation / AI log / retro

Nguồn: Ticket-03 đầy đủ do người dùng dán, Contract1.2. Không suy đoán Phase4.
ADR0003 ghi quyết định trước code về integer fuel, state machine và dawn.

## Thay test có lý do

58hành vi regression v1.1 được giữ trong test_contract_v12.py; 25test mới
ở test_fuel_v12.py, tổng83. Không skip/expectedFailure để giấu lỗi.

| Kỳ vọng bị thay | Cách cập nhật |
|---|---|
| Manifest1.1 và300/330/360s | 1.2 và240/270/300s, thêm tuning dầu/capacity/ratio |
| Snapshot tick120 còn298s | Còn238s, vẫn cùng cadence/input/60Hz |
| 4mote nạp40điểm;10mote+đèn200 | 20 và150 theo +5/mote, first+100 |
| Win bonus thời gian / all_lit | Test dawn và fuel-floor; thắng tick cuối là dawn_survived |
| Ba fixture win-night1/2/3 thắng bước1 vì all_lit | Thay bằng6fixture ngưỡng dawn won/lost,
  all-lit-running, expiry/dawn-relight; không tiếp tục chạy kỳ vọng early-win |
| Bot cũ dừng khi đủ5đèn | Challenge maintenance120s có fixture minh bạch,
  đi/nạp/châm bằng input hợp lệ tới dawn; không gọi đó là màn mặc định |

Hit/drop, move/jump/dash/camera, maps/pads/ramps/tower/wind, drifters/charm,
input validation/persistence/pause, deterministic và các trường snapshot cũ
đều còn test. Tag/proof Phase1–2 giữ nguyên, không sửa output cũ.

## Lỗi và quyết định AI đáng ghi

- Giữ logic chuẩn theo thứ tự: dầu/drain/out trước pickup/interact; khi fuel
  vừa tắt vẫn có thể relight trong chính tick dawn, rồi mới xét thắng.
- Snapshot100.0 không luôn là đèn đầy:5999unit<6000. Test ceil refuel dùng raw
  units, không sửa thành so sánh số làm tròn để ép full-skip.
- Drain thưởng tổng15, không +5+15; tỉnh stun trở về wander một bước.
- Xem ảnh thật phát hiện font máy thiếu ⚠ (hiện ô vuông). Thay glyph bằng
  tam giác/dấu chấm vẽ vector trong backend, giữ chuỗi cảnh báo để test nội dung.
- Stress tất cả đèn sáng và đủ shade có lúc Đêm2<30FPS. Dùng một polygon
  lồi cho mặt đĩa phẳng thay quạt tam giác, giữ hình học/collision và luật.
  Đo lại, chỉ nhận đạt sau khi gate thực sự pass. Không giảm số enemy/tuning.

## Kết quả / giới hạn

83test và28scenario deterministic đạt. Maintenance fixture120s sống đến dawn,
3/5đèn,3lửa,580điểm; CLI replay khớp. Full-night chạy đủ14400/16200/18000step
dưới30s. GUI có palette saved/modelunchanged, warning, fuel1Hz on/off/refill,
capacity16, flow/reset/audio routing. FPS/source/máy tại JSON.

Các flow3Đêm dùng scenario dựng đèn và time1tick để test UI, không phải video
người chơi. Maintenance là scenario có đèn/mote cho sẵn, không giả thành
default-map playthrough. Chưa có test ẩn, human listening/play/reviewer độc lập.
CI được kiểm tra sau push, không khẳng định dựa vào agent nói suông.

## Token / chi phí / retro

Không có token meter hoặc billing. Ước lượng thô **20k–45k token nội dung làm
việc Phase3** (mã/trao đổi/output), không gồm toàn bộ context reload và không
phải số đo chính xác. Chi phí tiền chưa xác định. Không dùng sub-agent.
Tiết kiệm bằng tái dùng83test/replay harness và sửa lớp state nhỏ thay đổi engine.

Bài học: luật thay thế cần tách history khỏi current state (ever_lit/relit_count),
và không dùng giá trị làm tròn cho điều kiện game. Đếm tick riêng giúp pause
đóng băng cả drain. Visual QA bắt lỗi font mà unit test string không thấy.
Nếu làm lại: đo stress tất cả đèn sáng sớm và chuẩn bị người review chơi/nghe thật.
