# Bằng chứng Phase 1

Mọi log/JSONL dưới đây do chương trình chạy thật tạo ra; không sửa tay để
đổi kết quả. Tái tạo: `python3 tools/verify.py`. Source hash trong
`verification.json` chuẩn hóa CRLF→LF để đối chiếu cùng mã ở các OS.
Timestamp/timing/môi trường có thể khác khi chạy lại; scenario JSONL phải
giống byte với cùng Python/mã/seed/input.

| Yêu cầu | Bằng chứng | Kết quả |
|---|---|---|
| 5 đèn, tuning, input/camera/jump, capacity, deposit, pulse, chase, damage, timer, JSONL | [tests.txt](tests.txt) | 31 test đạt |
| Nhặt 10 đom đóm, nạp và sáng L1 | [pickup-deposit.jsonl](pickup-deposit.jsonl), input ở tests/scenarios | Đạt |
| Pulse tốn sáng/choáng/đẩy | [pulse.jsonl](pulse.jsonl) + test | Đạt |
| Thắng/thua/no_flames/dawn và dừng sớm | [win](win.jsonl), [loss](loss.jsonl), [dawn](dawn.jsonl) | Đạt |
| Tất định | [verification.json](verification.json), SHA-256 5 replay, mỗi replay chạy hai lần | Đạt |
| Chơi màn mặc định từ đầu đến thắng | [full-play.json](full-play.json), [inputs](full-play.inputs.json), [JSONL](full-play.jsonl) | 5/5 đèn, 1.543 tick, 1.688 điểm, 2 lửa |
| Build/test/lượt chơi ở thư mục sạch | [clean-check.txt](clean-check.txt) | Đạt trên Windows/Python hiện tại |
| Desktop khởi động, input, pause, thắng/thua, reset | [gui-smoke.json](gui-smoke.json), [Canvas xuất PS](desktop-canvas.ps) | Programmatic smoke đạt |
| Phối cảnh 3D, nón lá/đèn nhỏ, HUD, sáng dần | [ban đầu](scene-start.png), [hai đèn sáng](scene-lit.png), SVG cùng tên | Đã xem và sửa lỗi ground pass |
| Hiệu năng headless 18.000 bước, spawn bật | [benchmark.jsonl](benchmark.jsonl), thời gian/máy trong verification.json | Đã đo, không nhận là ngưỡng Ticket-04 |
| macOS/Linux runtime | Workflow CI đa nền tảng | Cần xem kết quả CI thật sau push |
| Chơi tay, video, đánh giá độc lập | Chưa có | Chưa xác minh |

Ảnh PNG/SVG là **offscreen exports** từ cùng Scene.draw của desktop, không
phải ảnh chụp màn hình hay clip người chơi. `gui-smoke.py` thực sự tạo cửa
sổ Tk, chạy input adapter, cập nhật mô hình và kiểm tra Canvas. Lượt chơi
bot dùng màn gốc, không override scenario hoặc tài nguyên, rồi phát lại
bằng CLI chuẩn. Các loại bằng chứng này có phạm vi khác nhau, không thay
thế review cảm giác chơi của người thật.

Để phát lại lượt thắng:

```bash
python3 game.py --headless --seed 12 --night 1 --inputs docs/proof/phase-1/full-play.inputs.json --ticks 18000 --snapshot-every 120 --out replay.jsonl
```

Chưa có test ẩn của giảng viên để xác nhận. Không ghi đã đạt phase sau,
không có Release v1.0.0/video trước khi nhận Ticket-04.
