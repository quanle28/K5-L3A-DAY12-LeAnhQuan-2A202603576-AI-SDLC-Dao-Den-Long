# Nguồn và giấy phép

- Nhân vật Mây, Đảo Đèn Lồng, Đảo Bến, Bóng Mực và yêu cầu lab: tài liệu
  gốc Day 12 của VinUni-AI20k và PRD-0 do người dùng cung cấp. Giữ nguyên
  quyền của bên cung cấp với đề bài; LICENSE của mã triển khai không tái cấp
  quyền cho nội dung đề bài.
- Mã triển khai và mô hình hình học trong repo: viết cho bài của Lê Anh Quân
  với trợ giúp Codex/OpenAI trong hội thoại này. Không sao chép bài học viên khác.
- Hình ảnh game: tạo bằng các khối, hình nón, phép chiếu và màu trong view.py;
  không tải model, texture, ảnh, nhạc hoặc asset game khác. Không dùng ImageGen.
- Python/Tkinter/Tk: thư viện/runtime của máy, theo giấy phép tương ứng.
  Font Segoe UI của Windows hoặc font thay thế trên hệ điều hành, không phân phối font.
- Pillow: chỉ công cụ QA tùy chọn để xuất PNG, giấy phép HPND/MIT-CMU;
  không đóng gói hoặc cần cho game/headless. PNG từ renderer được ghi rõ là
  offscreen, không giả làm ảnh chụp phiên chơi trực tiếp.
- Không có âm thanh hay asset bên ngoài cần CC-BY attribution trong bản Phase 1.

## Bổ sung Phase 2

- Pygame2.6.1 (SDL/SDL_mixer): renderer/input/audio runtime, theo LGPL2.1
  và giấy phép thư viện đi kèm bản phân phối. Cài từ PyPI qua requirements.txt,
  không commit runtime binary. Tài liệu API chính thức:
  https://www.pygame.org/docs/ref/draw.html và https://www.pygame.org/docs/ref/mixer.html.
- Nhạc3Đêm/SFX: PCM tự tổng hợp từ các nốt sin trong audio.py, viết riêng cho
  repo bằng Codex; không tải sample/nhạc ngoài. Có metadata nguồn trong mã.
- Mô hình/tọa độ/bảng màu mới theo Ticket-02 do người dùng cung cấp; phần đề
  bài vẫn giữ quyền của tác giả lab. Font hệ điều hành được dùng tại runtime,
  không đóng gói font. Không cần Pillow hoặc Tkinter cho bản Phase2.

## Bổ sung Phase 3

- Luật dầu/drain/dawn và màu accessibility theo Ticket-03 người dùng cung cấp.
- Tam giác cảnh báo/dấu chấm, giấy rách/xẹp, fuelbar và tối ưu polygon lồi
  tự viết trong renderer; không tải icon, font, texture hoặc asset bên ngoài.
- Giữ nguồn/giấy phép của runtime và nội dung đề bài như các mục trên.

## Bổ sung Phase4 / Release

- psutil6.1.1, BSD3-Clause: đo RSS; không cần cho headless gameplay.
- PyInstaller6.11.1, GPL2.0 với bootloader exception: công cụ build standalone;
  setuptools75.6.0 và hooks-contrib2024.11 dùng trong môi trường build.
  Runtime notices của Pygame/psutil được kèm trong ZIP/THIRD-PARTY.
- imageio-ffmpeg0.6.0, BSD2-Clause: công cụ dev ghi video, không phải dependency
  của game. FFmpeg/libx264 đi kèm công cụ dùng để encode MP4; không phân phối
  executable FFmpeg trong gói game. Không dùng footage hoặc âm thanh bên ngoài.
- Sprite Bóng Mực LOD, clipping, UI/leaderboard và phụ đề do mã trong repo sinh.
  Video ghi cửa sổ app, phím tự động đã công bố; không dùng model ảnh/video AI.
- Bản nguồn dùng font hệ điều hành. Bản standalone còn có font dự phòng
  freesansbold.ttf đi kèm Pygame (Copyright2002 Free Software Foundation,
  metadata ghi GNU GPL); tệp font là asset của bên thứ ba, không thuộc MIT
  của mã game. Nguồn: https://github.com/pygame/pygame/tree/2.6.1/src_py.
- Bản sao LGPL2.1 và license dependency lấy nguyên từ tag chính thức
  https://github.com/pygame/pygame/tree/2.6.1/docs/licenses, kèm GPL2 từ GNU,
  ở docs/licenses/pygame-2.6.1 và ZIP/THIRD-PARTY/licenses. Một số notice giữ
  cho đầy đủ bản phân phối Pygame dù game không dùng tính năng tương ứng.
