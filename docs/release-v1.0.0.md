# Đảo Đèn Lồng — Bình minh v1.0.0

Game3D ba Đêm; giữ đủ đèn sáng tới bình minh. Contract1.3, giữ gameplay1.2.

- Tải ZIP đúng hệ Windowsx64/Linuxx64/macOSarm64, giải nén cả thư mục và chạy
  DaoDenLong(.exe). Không cần Python. Linux/mac có thể cần `chmod +x DaoDenLong`.
  Linux buildUbuntu22.04; macOS14 chưa ký/notarize. Cài từ nguồn: xem README,3lệnh.
- Benchmark chuẩn200bóng/100đom đóm; soak10Đêm; bảng điểm top10 cục bộ;
  đổi phím, phụ đề/chỉ báo, giảm chuyển động, chữ lớn và bảng màu dễ phân biệt.
- Số đo Windows local: avg123.1FPS,1%low58.2FPS,load307ms; soak0crash,
  RSS16.27→16.34MiB. Máy giảng viên quyết định kết quả hiệu năng cuối cùng.
- 96test,28scenario deterministic và28CLI byte-identical Phase3;3hệ được CI kiểm tra.
- Đính kèm demo72s,bench.json,soak.json. Video live framebuffer với phím tự động,
  fixture được khai rõ; không phải bằng chứng chơi tay thắng toàn chiến dịch.

Tài liệu/credits/license/retro và raw frame times ở repository. Giữ tag phase-1…phase-4.
