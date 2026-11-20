# Retro — 4 phase cùng AI

Lê Anh Quân · 2A202603576 · 20/11/2026 (ICT). Tài liệu này tóm tắt quá trình
trong lịch sử repo, không thay thế log máy chạy và không khẳng định đúng hạn
lab khi chưa biết mốc giờ Coach. Đề được gửi lần lượt trong hội thoại; link
Claude ban đầu không đọc được nên chỉ triển khai theo nội dung người dùng cung cấp.

## Evaluation theo phase

| Phase | Điều đã kiểm chứng | Bài học / giới hạn |
|---|---|---|
| 1 | Lõi60Hz, headless deterministic, nhặt/nạp/pulse/hit/thắng thua, tag riêng và proof | Chốt input persistence/rising-edge và tick0 trước đồ họa. Đầu tiên chưa có số liệu chuẩn nên phải ghi giả định. |
| 2 | Ba bản đồ, số liệu chuẩn, lướt/bùa/Gió Lạc/pause, JSONL1.1, GUI/settings/audio, CI đa hệ | Kịch bản nhỏ kiểm riêng mỗi cơ chế dễ tìm lỗi hơn một lượt chơi dài. Chưa có người nghe/chơi thử độc lập. |
| 3 |83test,28scenario replay, maintenance120s, dầu/drain/relight/capacity/dawn và GUI | Phân biệt ever_lit với lit; dùng fuel integer1/60; xét chết trước thắng. Ca thắng sớm phải thay có ghi lý do, không skip. |
| 4 |96test,28CLI byte-identical Phase3, benchmark30s, soak10Đêm, GUI/persistence, clean install, MP472s, standalone/CI | Đo số thật và giữ raw dt; tối ưu không đổi luật. Số local không thay máy chấm và test ẩn. |

## Điều hiệu quả và điều chưa hiệu quả

Tách simulation khỏi rendering giúp headless không cần GPU hoặc Pygame. Hằng số
trong contract là nguồn dữ liệu dùng khi chạy, tránh spec ghi một kiểu còn game
chạy kiểu khác. Validation từ đầu bắt input/scenario sai với exit2 và không để
NaN lọt vào JSONL. Đối chiếu output hai lần, rồi đối chiếu tag Phase3 từng byte,
là bằng chứng mạnh hơn lời AI nói “đã giữ nguyên”.

Những lỗi AI tạo ra đã bị phát hiện bằng kiểm tra cụ thể. Ở Phase3, so sánh số
thực làm sai biên dầu30; chuyển sang units nguyên và bổ sung test chính xác
ở ngưỡng. Thưởng pulse vào drain ban đầu dễ cộng nhầm5+15; test buộc tổng15.
Ảnh QA phát hiện glyph cảnh báo bị thiếu, dù string test vẫn đúng; backend vẽ
tam giác vector giải quyết mà không đóng gói font có bản quyền.

Ở Phase4, bản benchmark đầu chỉ khoảng46FPS. Profile chỉ ra polygon có tọa độ
chiếu khổng lồ ngoài màn hình; clipping viewport trước rasterization và sprite
LOD dùng chung game/bench nâng bản30s lên123.1FPS trung bình,58.2FPS1%low.
Không giảm200bóng,100mote hoặc tắt ánh sáng thật để đạt số. Một test mới tự
giả định clock benchmark phải dừng, trong khi ticket chỉ cấm kết thúc; test
được sửa theo luật, state vẫn playing và dầu/sinh/nhặt/hit đều bất biến.

Executable đầu lỗi pkg_resources do bộ thư viện Python toàn cục của máy. Smoke
test thực thi phát hiện ngay thay vì phát hành ZIP chỉ vì build thành công.
Đóng gói chuyển sang venv sạch và khóa setuptools/hooks. Lỗi vendored backports
còn tồn tại; dùng nhánh đọc file mà pygame.pkgdata đã hỗ trợ khi không có
pkg_resources, không đóng gói setuptools vào runtime game; chạy lại executable
headless/export/soak và benchmarkGUI. Đây là ví dụ “cài được trên máy tôi” chưa đủ. Một lần
ghi script qua PowerShell làm tiếng Việt thành dấu hỏi; GUI assertion đã bắt
và được sửa bằng patch UTF-8. Các lần lỗi đều được giữ trong nhật ký hội thoại,
không sửa tay dữ liệu đo để biến thành đạt.

## Harness giúp nhiều nhất

AGENTS.md giữ thứ tự12bước, ưu tiên no_flames, biên XZ/height, luật dầu,
bằng chứng thật và không di chuyển tag cũ. Pre-commit chạy verify --check-only,
chặn commit nếu build/test/replay sai mà không làm bẩn proof. CI kiểm ba hệ và
GUI Linux/Xvfb; workflow release build từng kiến trúc, kiểm executable trước
upload. Những công cụ này hữu ích hơn một prompt dài yêu cầu “làm tốt nhất”.
Không dùng sub-agent hoặc một reviewer giả định; không có skill riêng được
tạo cho repo. Harness thực sự đã dùng là AGENTS, hook, scenarios và các script
gate; chúng được giữ trong lịch sử, không thêm để trang trí lúc nộp.

## Token / chi phí / lần sau

Không có API billing hay token meter của phiên này. Ước lượng **nội dung làm
việc**, không phải usage đo được và không gồm mọi lần nạp lại context:
Phase1 khoảng20–40k, Phase2 khoảng30–60k, Phase3 khoảng20–45k, Phase4 khoảng
30–65k; tổng khoảng**100–210k token**. Chi phí tiền chưa xác định; không tự quy
đổi raUSD vì không có giá/billing thực tế. Các khoảng này chỉ để phản ánh mức
sử dụng, có sai số lớn. Chi tiết trước đó ở notes từng phase.

Tiết kiệm bằng giữ engine nhỏ, tái dùng regression, đọc nhiều file liên quan
trong một lần, không sinh asset bitmap khi khối hình học đủ dùng, không gọi
sub-agent, chỉ chạy lại benchmark sau thay đổi ảnh hưởng phép đo. Gate nhỏ
chạy thường xuyên; stress/GUI/video chạy ở các mốc có thay đổi liên quan.

Nếu làm lại, tôi sẽ đo stress scene ngay khi chọn renderer, chuẩn bị môi trường
đóng gói sạch sớm hơn và bố trí người chơi/nghe thử thực sự. Video hiện tại ghi
cửa sổ thật với phím tự động và fixture công bố, không phải bằng chứng khả năng
thắng ba map bằng tay. Tôi còn cần tự chơi, hiểu các luật biên và giải thích
thiết kế khi Coach hỏi; AI không thay trách nhiệm cá nhân đó.
