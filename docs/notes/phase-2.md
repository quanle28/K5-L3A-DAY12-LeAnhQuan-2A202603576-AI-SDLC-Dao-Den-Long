# Phase 2 — đánh giá, AI log và retro

Nguồn đầy đủ: Ticket-02 người dùng dán trong hội thoại, đã có bảng chuẩn/RGB.
Bản chuẩn bị thiếu dữ liệu được giữ như lịch sử, không còn là trạng thái hiện tại.
Chỉ làm Phase2; không đoán Ticket-03/04, không backdate tag, giữ nguyên phase-1.

## Thiết kế và kiểm chứng

- Model stdlib 60Hz độc lập frontend; World giữ tọa độ/surface/ramp/tower/pad.
- Wall tick và sim_tick riêng; dùng sim counters cho pause/TTL/spawn/wind.
- Chia rõ12bước đúng ticket; spawn sau contact; setup không event/score.
- Giữ interface CLI, mở night1/2/3 và schema1.1; input/state validation hữu hạn.
- Pygame thay Tk, cài bản cố định2.6.1 local.runtime, headless không import nó.
  Framebuffer3D/audio dùng cùng model; source palette theo bảng chuẩn.
- Settings/Campaign có logic riêng dễ test. GUI menu/pause/intro/results/dawn
  được smoke thật qua input adapter; PCM tự tạo và test routing với mixer dummy.
- Gate: test hành vi,14scenario replay2lần, botNight1, benchmark fullnight,
  GUI FPS và stress population. Build/test/replay thư mục sạch độc lập cache.

## Hồi quy: vì sao thay test Phase1

31test cũ được thay/đưa vào58test v1.1. Không tắt để che lỗi; các giả định
đã bị ticket thay gồm:

| Kỳ vọng cũ | Kỳ vọng mới và bằng chứng |
|---|---|
| Capacity12,pickup1.2,interact2.5 | 10/1/2, thêm height gate1.5 |
| +10 khi nhặt | Nhặt không điểm; +10 mỗi mote nạp |
| Stun3s/push3ngay/CD1.5 | Stun120tick,push4qua15tick/CD180, tâm3Dfoot+.8 |
| Shade2m/s luôn chase | 4/4.5m/s, hysteresis12/18 và5state chuẩn |
| Invuln120/drop25%tan | Invuln90/dropfloor1/2, TTL480, nhặt lại từ bước sau |
| Radius32/chặn biên | Radius40, rơiY<-10/lost/wait60/respawn90invuln |
| Win ưu tiên trước mất hết lửa | no_flames > all_lit > dawn |
| Không pause headless | Tick tăng/sim_tick đông, đầy đủ paused/resumed |
| 75motes ban đầu/spawn1s | 20điểm khác nhau,24/30điểm chuẩn,spawn240tick/trần30 |
| Bot greedy seed12 thắng nhanh | Luật mới khiến bot cũ thua; bot tránh địch/dash/pulse
  dùng seed1, thắng chuẩn ở11107tick,1403điểm,3lửa; replay CLI khớp |

Các hành vi còn hiệu lực (tick0/cadence/CLI malformed/edge/persistence/yaw/
partial deposit/determinism/setup-no-score) đều có test v1.1 tương ứng.
Mã/tests/proof cũ còn nguyên tại tag phase-1, không chạy nguyên kỳ vọng cũ
với luật mới rồi gọi đó là regression đã đạt. Test ẩn không được cung cấp.

## AI đã sai và sửa thế nào

- Bảng chuẩn thiếu ở bản gửi đầu: đã hỏi, chưa tự điền. File.md được nhắc
  lúc đầu0byte; dùng bản đầy đủ sau đó người dùng dán làm baseline.
- Batching lệnh Tk không cải thiện FPS: đo thật rồi bỏ, không nhận đạt30FPS.
- Shade scenarioY=0 bị coi như chân âm do trừ offset. Thêm test chaseY0 và
  giữ offsetY scenario theo mặt nền; không sửa output để che lỗi.
- Dash lên dốc bị chặn vì bước lên được hardcode. Sửa giới hạn theo độ dốc,
  giữ test tường đứng không vượt. Thêm test riêng cho dash lên ramp.
- Hai entity trùng vị trí: shade chase tự bước+X trước hit, làm sai recoil2m.
  Chặn overshoot/chuyển động khi distance0, test recoil60step đạt.
- Review pulse khi safe ejection: xử lý đồng thời push trong15step thay vì
  để hết ejection mới đẩy. Mọi thay đổi logic chạy lại gate thật.
- Tool cũ mặc định xuất proof phase1: đổi tất cả đường ghi sang phase2;
  hook --check-only vẫn ghi thư mục tạm. Phase1 files/tag không thay đổi.
- GUI test mũi tên từng giả định L1 gần origin nhất; tọa độ chuẩn làm tròn
  khiến L3 gần hơn một chút. Sửa fixture chỉ còn L1 chưa sáng để kiểm tra
  đúng nhánh offscreen, không đổi tọa độ hoặc logic chọn đèn để ép test đạt.

## Kết quả và phạm vi bằng chứng

58test,14scenario deterministic, botNight1 và3fullnight benchmarks đạt.
GUI/campaign/settings/HUD/audio routing đạt; renderer normal và stress
đều≥30FPS1280×720 trên máy local. Thời gian/máy/driver/độ dài mẫu có trongJSON.
Framebuffers là ảnh game thật do smoke xuất, không phải video chơi tay.
Màn Bình Minh/flow được kiểm tra bằng scenario đèn dựng sẵn, không giả làm
lượt chơi từ đầu cả3Đêm. Lượt chơi không override hiện có cho Đêm1.
Audio dummy không chứng minh người thật đã nghe trên loa. Chưa có reviewer
độc lập. CI đa OS kiểm tra sau push; không nhận CI đạt trước khi quan sát.

## Token / chi phí / retro

Không có billing hoặc token meter hệ thống. Ước lượng thô **30k–60k token
nội dung làm việc Phase2** (trao đổi/code/tool output), không phải số đo
chính xác và không gồm toàn bộ context reload. Chi phí tiền: chưa xác định.
Không dùng sub-agent trong phiên này. Tiết kiệm bằng stdlib headless, backend
renderer cùng abstraction, một bộ fixture/gate thay vì nhiều script rời.

Điểm hiệu quả nhất là có thứ tự tick và số liệu chuẩn trước khi thiết kế.
Test biên/trạng thái tìm lỗi mà clip đẹp không tìm được; profile thật tránh
giữ phương án batching chậm. Nếu làm lại: chọn backend đáp ứng âm thanh/FPS
ngay khi đọc ticket, tách geometry sớm, chuẩn bị người chơi/reviewer để xác
minh cảm giác điều khiển và nghe nhạc trước deadline.
