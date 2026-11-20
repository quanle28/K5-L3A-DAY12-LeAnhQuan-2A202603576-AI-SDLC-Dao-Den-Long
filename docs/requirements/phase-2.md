# Ticket-02 — Feature + chuẩn hóa, Contract v1.1

Nguồn: phần Ticket-02 người dùng dán trong hội thoại. Mục tiêu tag `phase-2`.
Trạng thái: **đã nhận đầy đủ bảng chuẩn và RGB trong hội thoại**;
baseline thực thi tại [phase-2-standard.md](phase-2-standard.md).
Tag phase-1 giữ nguyên, không viết lại lịch sử/bằng chứng đã công bố.

## Lịch sử làm rõ thông tin

1. Bảng số liệu chuẩn ở Phần 1: tuning, duration mỗi đêm, jump/gravity/dash,
   rơi/mất lửa/mất đồ/respawn, pulse, pickup/deposit, lịch motes và các trạng
   thái/timing/radius của Bóng Mực. Ticket có tham chiếu bảng nhưng không kèm.
2. Bảng RGB chuẩn cho các thành phần được nhắc ở mục 8 chưa có các dòng giá trị.
3. Nếu nguồn có thêm schema scenario v1.1 (drifters/charms/motes), cần giữ
   đúng tên field, trạng thái và đơn vị thay vì tự sáng chế giao thức test.

Ba mục trên đã được giải quyết bằng nội dung đầy đủ người dùng dán sau đó.
Phần schema còn chưa quy định chi tiết được ghi minh bạch trong giả định bên dưới.

## Kế hoạch kiểm chứng trước triển khai

| ID | Tiêu chí nghiệm thu | Kiểm chứng dự kiến |
|---|---|---|
| S01 | Mọi tuning khớp số chuẩn; điểm +10/mote NẠP, +100/đèn, +5/shade trúng pulse; bonus thắng chuẩn; tổng chỉ cộng đêm thắng | So bảng chuẩn + test scoring/setup/replay |
| S02 | Thực hiện đúng 12 bước trong ticket; spawn tick này chỉ tương tác từ tick sau | Scenario chạm/pulse/deposit/spawn cùng bước |
| S03 | Pause xử lý trước countdown/move; tick tăng nhưng sim_tick/timer/TTL/cooldown/spawn đứng yên | Scenario pause/resume + snapshot mọi tick |
| M01 | Đêm 1 bán kính40, 5 đèn đúng tọa độ, 24 điểm motes, 12 điểm shade; shade spawn5s rồi8s, cap6, cách Mây≥15 | Snapshot map, test lịch/điểm spawn/fall |
| M02 | Đêm2 hai đảo R28 tâm0/70, cầu x26…44,z±2; 6 đèn đúng tọa độ | Test biên đảo/cầu và snapshot |
| M03 | Hai bục Đêm2 radius1 tại(20,0,18)/(50,0,-18); vy14/vxz24 tới tâm kia, giữ tới đáp, dash vẫn hoạt động | Scenario launch, khóa hướng/landing/dash |
| M04 | Đêm2 điểm motes/shade đúng mỗi đảo; shade7s cap8 | Test map/spawn |
| M05 | Đêm3 R45, tầng0/1/2 và hai dốc30°/150° rộng3 đúng cao; vách không bước lên; bước ra rơi xuống | Scenario tường/dốc/đáp/tầng |
| M06 | Bục(0,3,13) phóng vy12/vxz8 hướng-Z; tháp trụR2 cao8 không leo; 7 đèn chuẩn | Scenario launch/tower/lamps |
| M07 | Đêm3 có30 điểm motes đúng tầng,16 điểm shade; shade6s cap10 | Snapshot và test lịch |
| M08 | Gió30s/lần,5s, đẩy2m/s, báo trước2s bằng lá/âm; RNG deterministic, wind_enabled false tắt | Scenario gió/nhảy/pause và review nghe/nhìn |
| F01 | Gió Lạc Đêm2/3 spawn tick1200/2400…, cap2, ID D*, idle2/chase7/flee7; chase iff carried≥5 và d≤15 | Scenario spawn/chase/idle/pause |
| F02 | Gió Lạc cướp min(3,carried) khi XZ≤1.2, một lần/con; flee240tick rồi removed; không hit, không bị safe/invuln cản | Scenario steal đồng thời shade hit và safe zone |
| F03 | Pulse chase→flee không cướp; pulse flee mang đồ→drop toàn bộ, biến mất sau120tick | Scenario pulse/drop/TTL/repeated-pulse |
| F04 | Bùa C1/C2 chuẩn vị trí; nhặt cùng luật motes;600tick, refresh; speed7.2; dash14 trong12tick không cooldown, không nhận dash khi đangdash; respawn2700tick | Scenario charm/pause/refresh/dash/respawn |
| F05 | Menu→giới thiệu(Ông Đăng)→chơi→kết quả→đêm sau; thắng3 ra Bình Minh/tổng; thua retry đêm đó | GUI flow smoke + chơi thử |
| F06 | Esc/P pause có Tiếp tục/Retry/Cài đặt/Menu; không chạy logic khi pause | GUI smoke + scenario headless |
| F07 | Âm lượng/độ nhạy chuột lưu qua lần mở; chỉnh chuột có tác dụng | Test config roundtrip, GUI restart |
| F08 | Nhạc đêm, SFX pickup/lit/pulse/hit/jump/dash/win/loss/spawn/countdown10s | Event→audio tests + nghe thử thật |
| F09 | HUD vị trí chuẩn,10ô, cooldown, E prompt, mũi tên đèn ngoài màn; timer≤30s đỏ/nháy | Ảnh1280×720 và GUI test |
| F10 | RGB chuẩn sai≤10%/kênh; ambient=.15+.55*(lit/count) | Test palette/ambient, ảnh lit0/partial/all |
| C01 | Contract1.1; night1/2/3; snapshot thêm night/wind/player vel,grounded,invuln,CD,charm; motes/drifters/charms đúng schema | CLI/schema tests mọi đêm |
| C02 | Scenario mới, counters, shade state đúng spawning/wander/chase/recoil/stunned; drifters/charms replace; flags mới | Setup/validation tests, no setup score/events |
| C03 | dash/pause rising-edge, event mới đúng name/data; player_hit fall có lost | Scenario từng tính năng mới, event schema |
| Q01 | 21.600tick một đêm headless≤30s | Benchmark subprocess timeout30, ghi steps/máy/exit |
| Q02 | ≥30FPS trung bình1280×720 | Benchmark gameplay/render/update GUI thực, ghi resolution/sốframe/máy |
| Q03 | Test Phase1 còn hiệu lực đạt với số chuẩn | Port test sang tuning mới; thay test yêu cầu cũ có ghi lý do |
| D01 | Spec/AGENTS/harness cập nhật, scenario mỗi tính năng, proof đúng commit, tag publicphase2 | Gate, git history, replay |

## Thay đổi đã chắc chắn so với Phase 1

- Điểm per_mote chuyển từ **nhặt** sang **nạp**; per_stun20→5. Phải thay test
  scoring liên quan, không tắt test âm thầm.
- Đảo Đêm1 radius32/chặn biên→radius40/có rơi; đèn đổi sang tọa độ chuẩn.
- Bóng Mực chase/stunned đơn giản→state machine chuẩn đủ5 tên; lịch spawn mới.
- GUI pause trước đây ngừng gọi model→headless v1.1 vẫn chạy tick nhưng đóng băng sim_tick.
- GUI Esc trước đây thoát→pause; flow một đêm→campaign3 đêm. Giữ quit trong menu.
- FPS Phase1 chưa đạt ngưỡng mới; tối ưu là việc bắt buộc trước nghiệm thu.

## Quyết định cho chỗ ticket chưa quy định chi tiết

- Mọi tọa độ chuẩn được giữ trong World; start Đêm3 chọn (0,0,-30) vì nguồn
  chỉ chỉ định spawn (0,0,0) ở Đêm1; tránh spawn trong tầng2/tháp chuông.
- Bóng Mực mới có spawning30tick; scenario không ghi state thì chase hoạt động
  ngay, đúng cách dựng kiểm thử từ v1.0. Wander dùng tốc độ chuẩn và đường lượn
  tất định. Chênh Y của shade do scenario đặt được giữ nguyên khi đi trên cùng tầng.
- Shade ID có hậu tố số được xét theo thứ tự tự nhiên S1,S2,…,S10; tie đèn theo ID.
- Gió Lạc idle/chase đều có thể cướp khi va chạm và Mây còn đồ; điều kiện ≥5/15m
  chỉ quyết định chủ động đuổi. Flee không cướp lại. Quyết định này theo câu
  "Chạm…cướp min(3,đang mang)", kể cả khi mang dưới5 hoặc hai con chạm cùng bước.
- Scenario drifter nhận id,pos,state,stolen,state_ticks_left; charm nhận id,pos,
  available,respawn_ticks hoặc respawn_s; id chuẩn C1/C2 có thể bỏ pos để giữ vị trí
  mặc định. Mote nhận cả [x,y,z] v1.0 và object id,pos,kind,ttl_ticks/ttl_s v1.1.
  Random motes có ttl_s0 (không hết hạn), dropped có TTL480tick. Không dựng điểm/event.
- Khi rơi: player_hit by=fall,dropped=0,lost=số mang trước rơi. Không sinh đồ nhặt
  lại. Trong wait60tick, các counter khác vẫn giảm; không pickup/touch/action.
- Random flags tắt tự dựng/spawn, không xóa danh sách tường minh. wind_enabled
  false tắt cả warning và force. Các timer dùng sim_tick, không wall tick.
- Nhạc/SFX là PCM tự tổng hợp, không dùng asset ngoài. Âm lượng/chuột lưu JSON
  ở ~/.lantern_island/settings.json; test dùng thư mục tạm, không sửa cài đặt thật.
- Backend Pygame thay Tk để đáp ứng FPS/audio; không thay số liệu hay protocol.

Kết quả nghiệm thu và giới hạn: [proof Phase2](../proof/phase-2/README.md).
