# Demo72giây

[demo.mp4](demo.mp4), H.264/yuv420p,1280×720,30FPS,72s, không âm thanh,
phụ đề tiếng Việt. Metadata do decoder đọc ở metadata.json; source ghi
tools/record_demo.py, encoder imageio-ffmpeg0.6.0 chỉ là dependency dev.

- 0–11s: menu/intro và một đoạn chơi map chuẩn, phím tự động qua input adapter.
- 11–20s: fixture đặt mote/đèn gần Mây; nhặt/thắp/capacity/pulse/refuel thực.
- 20–32s: accessibility, rebind conflict/defaults, thua fixture và lưu/đọc bảng điểm.
- 32–36s: xem trực tiếp map2/3; không giả là đã chơi thắng map trước.
- 36–56s: đầu ra unit test và CLI headless thực sự chạy ngay trước khi ghi clip.
- 56–65s: cảnh benchmark thật, số30s từ bench.json đo riêng không encoder.
- 65–72s: kết quả soak thật từ soak.json và vị trí bằng chứng.

Video dùng framebuffer cửa sổ Pygame và60logic tick/s, đồng hồ capture30FPS.
Không phải clip người chơi tay hoặc full-campaign playtest. Khung PNG chọn
được lưu để QA chữ/bố cục; không dùng để dựng thay video live.
