# PRD-0 / Test Contract v1.0 — phân tích yêu cầu

Nguồn: nội dung người dùng dán ngày 20/11/2026 từ
[lab board](https://claude.ai/artifact/Q1RYyv1dxjUczzCbd2ZnoW).
Đây là bản phân tích/nghiệm thu, không phải ticket tự đặt cho phase sau.

## Tiêu chí nghiệm thu lập trước code

| ID | Yêu cầu | Kiểm chứng |
|---|---|---|
| P1-01 | Đêm 1 Đảo Bến tròn, đúng 5 đèn | test manifest, khởi tạo, ảnh |
| P1-02 | Mây di chuyển/nhảy, camera 3D, nón lá, đèn nhỏ | test camera/jump, GUI smoke, ảnh |
| P1-03 | Nhặt, mang và nạp đom đóm vào đèn | pickup-deposit, test capacity/partial deposit |
| P1-04 | Bóng Mực sinh ra, đuổi, chạm mất lửa | test chase/hit/invuln/spawn |
| P1-05 | Tỏa sáng tốn sáng, xua Bóng Mực | pulse scenario, test cooldown/edge/stun/push |
| P1-06 | Đèn sáng chặn Bóng Mực | test safe zone |
| P1-07 | Thắng, thua, điểm, HUD, chơi lại | win/loss/dawn, full-play bot, GUI smoke |
| C1-A | Manifest đúng tuning runtime | runtime đọc trực tiếp manifest |
| C1-B | Headless 60Hz và đủ CLI | CLI subprocess, replay |
| C1-C | Input giữ trường, tick tăng, yaw/vector, false→true | input/camera/edge tests |
| C1-D | Override đúng, L1…L5 theo ID, setup không score/event | setup/validation tests |
| C1-E | JSONL/tick/field/rounding, deterministic | cadence/zero/rounding/replay byte-for-byte |
| D1 | README ≤3 lệnh, harness, notes, proof, public tag | kiểm tra bàn giao/Git |

## Contract bắt buộc đã đối chiếu

```text
<headless_cmd> --seed <int> --night 1 [--scenario <file.json>]
  [--inputs <file.json>] --ticks <int> --out <file.jsonl>
  [--snapshot-every <int, mặc định 10>]
```

- Headless không import Tkinter, không dùng cửa sổ/GPU/clock thực; 60Hz.
- Tick 0 sau setup, trước input. Bước k đọc input tick k, phát event tick k+1.
  sim_tick=tick, time_left_s=duration-tick/60. Dừng đủ bước hoặc terminal.
- Input move mặc định [0,0], yaw 0, nút false. Trường vắng giữ nguyên;
  frame.tick tăng nghiêm ngặt; nút false→true mới kích hoạt. Công thức:
  x'=x cosθ+z sinθ, z'=-x sinθ+z cosθ. Chỉ vector >1 mới chuẩn hóa.
- Y hướng lên; player.pos là chân, lantern.pos là chân cột, shade.pos là tâm,
  mote.pos là điểm đất. Khoảng cách XZ, không cộng kích thước, dùng <=r.
- Scenario player pos/carried/flames; random_motes/shades; motes/shades thay
  danh sách; lanterns cập nhật L1…L5 theo ID; time_left_s. Thiếu dùng mặc định.
  Setup không phát event hay cộng điểm. lit:true được dựng sẵn, không thưởng.
- Snapshot từ tick 0 rồi mỗi snapshot-every, đủ type/tick/sim_tick/state/
  time_left_s/score/player/lanterns/shades/motes_active, thêm motes[id,pos].
- Event đúng tên/data: mote_picked[carried], deposit[lantern_id,amount,deposited],
  lantern_lit[lantern_id], pulse[stunned_ids], player_hit[by,flames,dropped],
  shade_spawned[id], game_over[result,reason]. Tọa độ 3 chữ số thập phân.
- State playing/won/lost; shade chase/stunned. Dòng cuối end[ticks,state,score].
  Cùng seed/scenario/input cùng byte output, kể cả ID tự sinh.
- Exit 0 bình thường; file inputs/scenario sai exit 2 + stderr; lỗi output exit 1.

## Giả định cho chỗ PRD mở

Thông số duy nhất ở game.contract.json. Đảo bán kính 32m, đèn vành 21m,
Mây bắt đầu (0,0,0). 75 đom đóm ban đầu gồm 5 đường dẫn và rải ngẫu nhiên;
thêm 1/giây nếu dưới 100. Ba Bóng Mực, thêm 1 mỗi 12 giây, tối đa 12.
random_* false tắt danh sách tự dựng và sinh thêm; danh sách tường minh vẫn dùng.

E nạp từng phần, tối đa số mang/phần còn thiếu, chọn đèn chưa sáng gần nhất
(hòa chọn ID). F chỉ khi đủ cost và hết hồi chiêu, tốn cost cả khi trượt;
mỗi Bóng Mực trúng thưởng per_stun, kể cả choáng lại. Trùng vị trí đẩy +X.
Chạm nhiều Bóng Mực một bước chỉ mất một lửa. Rơi floor(carried*ratio),
biến mất trong sương, không nhặt lại để tránh farm điểm. Nhảy chỉ đổi Y,
không miễn sát thương XZ. Rìa đảo chặn, không phạt rơi. Dash không có.

Thứ tự bước: di chuyển/nhảy → nhặt → nạp → pulse → Bóng Mực đuổi → thắng
→ sát thương/thua → sinh định kỳ. Thắng ưu tiên nếu thắp đèn cuối đúng bước
bình minh. Chỉ khi thắng thưởng floor(time_left_s)*per_second_left và
flames*per_flame_left, cộng một lần. GUI pause không chạy bước.

## Thay đổi so với bản tạm trước PRD

Bản tạm 3 đèn/local-baseline-0 chưa commit hay nghiệm thu; đã thay hoàn toàn
bằng 5 đèn, capacity, nạp từng phần, pulse/chase, timer/score, JSONL v1.0.
Không dùng bản tạm làm proof. Ticket-02/03/04 chưa nhận nên chưa triển khai.
