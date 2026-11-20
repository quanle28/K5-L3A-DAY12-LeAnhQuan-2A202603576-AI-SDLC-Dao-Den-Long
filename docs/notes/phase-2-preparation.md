# Chuẩn bị Phase 2 — chưa nghiệm thu

**Ghi chép lịch sử lúc chưa nhận đủ nội dung.** Bảng chuẩn đã được người dùng
bổ sung sau đó; triển khai/kết quả hiện tại ở phase-2.md và docs/proof/phase-2.

Đã đọc phần Ticket-02/v1.1 người dùng gửi và lập acceptance criteria cho
bản đồ, các tính năng mới, contract, hồi quy, hiệu năng và bàn giao tại
docs/requirements/phase-2.md.

Thiếu bảng số liệu chuẩn Phần 1 và mã RGB của bảng màu. Đã yêu cầu bổ sung;
không dùng số Phase 1 hoặc tự đặt thay cho số chuẩn. Manifest/runtime vẫn1.0.

Chuẩn bị độc lập: đo renderer thực ở 1280×720, gồm simulation, xoay camera,
vẽ Tk và cập nhật display. Đã thử gửi các lệnh vẽ theo batch, kết quả khoảng
15 FPS, không tốt hơn direct khoảng16 FPS, nên đã bỏ thử nghiệm khỏi game.
Log thật ở docs/proof/phase-2/renderer-preparation.json, không nhận đạt30FPS.
tools/benchmark_renderer.py hiện dùng để tái đo baseline direct. Kết quả
batch trong log là thử nghiệm đã loại bỏ, không phải backend đang sử dụng.

Đã chạy tools/verify.py --check-only:31 test và các replay Phase1 vẫn đạt.
Không ghi đè bằng chứng Phase1, không di chuyển tag hoặc push tagphase2.
Chưa triển khai luật mới phụ thuộc bảng số liệu chưa nhận.
