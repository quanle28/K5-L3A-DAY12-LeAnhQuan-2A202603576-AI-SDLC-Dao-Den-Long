# Bằng chứng Phase4 / Contract1.3

Mọi output ở đây được tạo bằng chạy chương trình; không sửa số liệu cho đạt.
Ngày20/11/2026 ICT, Python3.9.7 / Windows10.0.22631 local. Tuning/gameplay
vẫn1.2; tag/proof Phase1–3 không bị ghi đè.

| Yêu cầu | Bằng chứng |
|---|---|
| Benchmark chuẩn1280×720,200/100/3lit100,orbit/warm3/measure30 | [bench.json](../../../bench.json),[rawdt](../../../bench.samples.json),test benchmark invariants/orbit/statistics |
| Hiệu năng local | avg123.0739FPS,1%low58.2392FPS,p95=10.8581ms,load307.169ms,RSSpeak53.781MiB |
| Soak10Đêm cùng tiến trình | [soak.json](../../../soak.json):10kết quả,seed7…16,PID6612,crashes0,RSS16.2734→16.3438MiB (+0.43%) |
| Gameplay regression | [tests.txt](tests.txt):96test;[verification.json](verification.json):28case deterministic+fullnight;[phase3-regression.json](phase3-regression.json):28CLI byte-identical với tagphase-3 |
|3Đêm GUI/FPS/palette/audio | [gui-smoke.json](gui-smoke.json),night1/2/3.png,colorblind-low-on/off.png,refueled.png |
| Đổi phím/persist/báo trùng/reset | Unit release tests + GUI adapter;[bindings-large.png](bindings-large.png) |
| Chữ18px/lớn1.25/giảm chuyển động | Font telemetry trong GUI assertions;[settings-large.png](settings-large.png); renderer tắt bob/lá/pulseexpansion |
| Phụ đề và chỉ báo | [shade-notice.png](shade-notice.png),[wind-notice.png](wind-notice.png),hud-danger.png và GUI assertions last10s/lowfuel |
| Top10/export/name/tie/score |13release test bao gồm validation,Unicode,tie timezone,persistence,corrupt backup,exportfreshprocess;[leaderboard.png](leaderboard.png) |
| Cài sạch | clean-check.txt do tools/clean_check.py sinh, không dùng runtime/cache repo |
| Gói phát hành/video | Workflow release3hệ, smoke executable;[demo72s](../../demo/demo.mp4),[metadata](../../demo/metadata.json) |

verification.json giữ SHA256 source chuẩn hóaLF để đối chiếu nguồn ở tag.
CI upload log riêng theo hệ, không giả outputlocal là số của Linux/macOS.
CI triển khai: [run44720616958](https://github.com/quanle28/K5-L3A-DAY12-LeAnhQuan-2A202603576-AI-SDLC-Dao-Den-Long/actions/runs/44720616958)
đã đạt cả3hệ và GUI Linux/Xvfb. Bản Windows độc lập có
package-windows-amd64.json/package-log.txt; standalone-benchmark-smoke.json
chỉ đo1s sauwarm3s để kiểm DLL/font/renderer của executable, không thay bench30s.
`tools/release_check.py` đối chiếu công thức với rawdt, ngưỡng local,soak,
proof/hashes/video/file manifest trước gắn tag.

Giới hạn: chưa có test ẩn hoặc cấu hình máy giảng viên; không có human playtest,
nghe loa hoặc review độc lập. GUI/campaign dùng fixture để đi qua màn hình kết
quả; audio dummy kiểm PCM/mixer. Cả10randomsoak thua là đúng đầu vào ngẫu nhiên,
không phải crash. Video có phím tự động/fixture minh bạch. Không xác nhận deadline
Coach dựa trên thời gian máy hay tự sửa lịch sử tag.
