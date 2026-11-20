# Phase 1 — nhật ký AI, đánh giá và retro

Học viên: Lê Anh Quân, 2A202603576. Công cụ: Codex/OpenAI trong hội thoại này,
Python/Tkinter, Git, GitHub connector. Không sử dụng bài của học viên khác.

## Quy trình và quyết định

1. Đọc sáu file gốc. Thử đọc board qua web/HTTP/UI, thất bại 403/native pipe.
   Người dùng yêu cầu tạm dừng; đã dừng. Không tạo tag trong lúc thiếu đặc tả.
2. Người dùng gửi PRD-0 và Contract v1.0, tiếp tục Phase 1. Bản nền tạm 3 đèn
   và JSON cũ được thay hẳn; không giữ làm nghiệm thu.
3. Lập acceptance matrix, chọn Python thuần để headless không phụ thuộc GUI,
   manifest là nguồn tuning duy nhất. Tkinter dựng phối cảnh 3D để tránh tải
   engine/asset và có đường chạy Linux/macOS.
4. Viết mô hình và runner theo tick/input/event chuẩn, thêm GUI dùng cùng logic.
   Viết test hành vi thật và scenario replay, không kiểm tra chỉ sự tồn tại file.
5. Chạy test/CLI/GUI smoke. Bot chơi màn mặc định qua input hợp lệ, xuất input
   và phát lại bằng CLI độc lập, không sửa tài nguyên hay vị trí.
6. Kiểm tra hình bằng bản xuất của renderer. Đo benchmark có môi trường,
   thử copy sạch, lưu log và hash nguồn. Chuẩn bị commit/tag Phase 1.

## Lỗi AI và cách phát hiện/sửa

| Vấn đề | Phát hiện | Sửa / harness |
|---|---|---|
| Bản nền trước PRD dùng 3 đèn và giao thức tạm | Đối chiếu PRD/Contract người dùng gửi | Thay toàn bộ, ghi nguồn/giả định; AGENTS yêu cầu đọc phase-1 trước code |
| Các tam giác đất lớn che chân nhân vật, vùng sáng bị đất đè | Xem PNG do chính renderer xuất | Tách các pass mặt đất → vùng sáng → vật thể; xuất lại ảnh kiểm tra |
| Dựng nhiều tam giác cho mỗi đom đóm làm Tk chậm | GUI smoke đếm item và đo thời gian | Dùng một billboard cho mỗi đom đóm, giữ mô hình 3D/camera; không đổi logic |
| Benchmark đầu dùng tình huống bình minh sớm | Review kịch bản và số bước thực | Đổi thành 301 giây, vùng đèn bảo vệ, chạy đủ 18.000 bước và assert số bước |
| Hook kiểm tra có thể làm bẩn proof sau stage | Review quy trình commit | --check-only ghi proof vào thư mục tạm, lỗi test vẫn chặn commit |
| Windows có alias python3 nhưng không có interpreter chạy được | Hook thực sự chặn commit vì python3 lỗi | Kiểm tra python3 --version thay vì chỉ tìm tên lệnh; fallback python |

Không có agent/người đánh giá độc lập trong phiên này. Các test và tự review
do cùng agent thực hiện; không nhận điểm mục đánh giá độc lập khi chưa có.

## Kết quả

- 31 test đạt; năm scenario chạy lại giống từng byte.
- Default seed 12 thắng 5/5 đèn ở tick 1.543, điểm 1.688, còn 2 lửa.
- GUI smoke đạt: cửa sổ, input, nhảy, pause, terminal overlays, reset.
- Copy sạch build/test/full-play đạt. Nguồn và môi trường có hash/log.
- CI đa nền tảng được cấu hình; chỉ ghi là chạy đạt khi có kết quả CI thật.
- Chưa có test ẩn, chơi tay, video hoặc reviewer độc lập; chưa suy đoán phase sau.

## Token và chi phí

Không có số đo token/billing của phiên được công cụ cung cấp. Ước lượng rất
thô cho nội dung làm việc Phase 1: khoảng **20.000–40.000 token**, dựa trên
độ dài trao đổi, mã và output; không phải số đo hệ thống, không gồm toàn bộ
chi phí nạp lại context. Chi phí tiền: **chưa xác định**, không tự đặt đơn giá.
Tiết kiệm bằng một mô hình logic dùng chung, Python stdlib, không tải engine,
scenario nhỏ và một lệnh verification thay vì lặp lại mọi kiểm tra thủ công.

## Retro và bàn giao cho phase sau

Contract trước code giúp bắt sai tick, input persistence và edge trigger sớm.
Bằng chứng có input/output/hash hữu ích hơn lời khẳng định. Renderer riêng
giúp phát hiện lỗi phối cảnh mà test logic không thấy. Nếu làm lại: dựng
khung kiểm tra hình ngay từ đầu, profile trước khi tăng số tam giác, và
chuẩn bị desktop/reviewer để chơi tay trước khi kết thúc phase.

Khi nhận ticket mới: lưu yêu cầu, ghi những giả định/test bị thay, cập nhật
manifest/logic và test, chạy hồi quy mọi phần còn hiệu lực, lưu proof riêng,
rồi mới gắn tag tiếp theo. Không backdate tag hoặc sửa lại lịch sử đã công bố.
