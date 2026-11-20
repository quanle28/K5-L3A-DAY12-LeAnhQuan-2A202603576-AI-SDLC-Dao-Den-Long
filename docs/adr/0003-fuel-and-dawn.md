# ADR-0003 — Dầu nguyên, đèn tái thắp và thắng tại bình minh

Trạng thái: chấp nhận. Nguồn: Ticket-03 đầy đủ do người dùng dán trong hội thoại.

## Vấn đề / thay thế

v1.1 coi đèn sáng là trạng thái cuối, thắng ngay all_lit, capacity10 và điểm
nạp10/stun5/bonus thời gian. Ticket-03 thay những luật này, không được tiếp
tục dùng test kỳ vọng cũ hoặc sửa tag/proof phase-1/phase-2 để trông như đã đạt.

## Quyết định trước triển khai

- Mỗi đèn giữ fuel_units nguyên: 60unit=1fuel, max6000. Decay1unit mỗi
  simstep; mỗi shade đang drain hợp lệ hút5unit/step. Không làm tròn trong
  quyết định đầy dầu/ngưỡng30/hết dầu; chỉ xuất fuel một chữ số thập phân.
- Lưu ever_lit và relit_count riêng với lit/deposited. Out reset deposited0,
  giữ lịch sử; lần đầu cost10/+100, tái thắp cost5/+40, mỗi mote nạp/châm +5.
- Step2 lấy các drain đang hoạt động trên đèn yếu trong2m, cộng dồn decay và
  drain, rồi extinguish trước move/pickup/interact. Event fuel_drain mỗi
  sim_tick chia hết60 (wall tick có thể khác khi pause), báo fuel sau tổng hao.
- Step5 có thể thắp lại ngay trong tick đèn vừa hết dầu. Chọn receiving lamp
  gần nhất rồi ID; lit100 thật sự không nhận. Vì step2 chạy trước tương tác,
  đèn100 lúc tick0 thành5999unit trong tick1 và có thể nhận1mote: không dùng
  số làm tròn100.0 của snapshot để quyết định nó đang đầy.
- Safe chỉ tồn tại khi lit và fuel_units>=1800. Refuel phục hồi safe trước
  pulse và AI. Shade trong vùng được eject≤30step, không hit khi eject.
- Chỉ wander chọn weak-lit nearest; không có weak thì tới unlit nearest.
  Chase giữ Mây làm mục tiêu; drain lưu target_lantern_id. Pulse thưởng tổng15
  nếu trạng thái trước pulse là drain. Hết stun về wander trong bước đó.
- Terminal duy nhất: no_flames trước; khi time<=0, sống và lit>=ceil(.6*n)
  thắng dawn_survived, còn lại dawn. Không all_lit hoặc thưởng thời gian.
- Capacity tính từ successful_lights của Đêm: min(20,10+2*n), kể cả relight.
  Scenario lit không tăng counter/score. Counter scenario được áp trước carried.
- Cài đặt colorblind chỉ thuộc frontend: lưu JSON, palette copy và hình dạng
  giấy rách/xẹp. Không đổi model, RNG hay JSONL theo cài đặt hiển thị.

## Nghiệm thu dự kiến / hậu quả

Test boundary30, hết dầu6000step, multi-drain, pause, full/refill/rounding,
expiry→relight cùng tick, dynamic capacity/cap20/setup, pulse drain15, ngưỡng
3/5–4/6–5/7, death-at-dawn và no-early-win. Retain regression physics/input/
drifters/charms/maps/FPS. GUI test bar/blink/shape/palette/settings persistence.

Scenario fuel thập phân được lượng tử gần nhất tới1/60 bằng Decimal/HALF_UP;
lit:true thiếu fuel mặc định100, lit luôn ever_lit:true. Unlit có fuel0.
Mọi dữ liệu setup không sinh event/score; relit_count setup0. Invalid drain
target ID bị từ chối. Trường hợp invalid target/high-fuel của drain chuyển
wander trước ejection; nếu target còn yếu thì Mây≤6 chuyển chase.
