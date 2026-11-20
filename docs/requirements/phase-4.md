# Ticket-04 — Bình minh / Contract v1.3 / Release v1.0.0

Nguồn: bản Ticket-04 đầy đủ do người dùng dán trong hội thoại. Không thay luật v1.2.
Tag phase-4 và Release v1.0.0 chỉ tạo sau nghiệm thu; giữ nguyên tag/proof1–3.

| ID | Nghiệm thu | Cách kiểm chứng trước code |
|---|---|---|
| B1 | Bench window1280x720,vsync off,Night1,200wander/100mote,3lit100fuel; disable spawn/damage/pickup/decay/end,player0 | Bench fixture/model invariants + framebuffer/window metadata |
| B2 | Camera(30cosθ,15,30sinθ),lookat0,15s/vòng,CCW,start+X | Camera coordinate tests |
| B3 | Warm3s, đo --duration (official30),frames/dt đúng avg,slow1%,p95,load/RSS | Pure stats tests + raw frame times + bench.json chạy thật |
| B4 | avg>=60,p1>=30,load<=10s trên máy chấm chung | Local actual measurements, không giả nhận thay máy giảng viên |
| S1 | Headless10night cùngprocess,1→2→3,seed7+i; direction30tick,prob5/3/2/10% | RNG/input tests + soak.json actual PID/roundtrip, memstart/end/reset |
| S2 | crashes0,RSS_end<=1.2RSS_start | Assert gate trên dữ liệu thật, không sửa số |
| L1 | Name3–12ASCII letters/digits/underscore (Unicode optional),scorewon-only,nights0–3,ISOtz,seed | Validation/tie sorting/top10/persistence tests |
| L2 | Loss hoặc sauDawn cho lưu; main menu leaderboard; export JSON CLI đúng thứ tự | GUI flow + fresh-process export tests |
| A1 | Rebind9actions, conflict notice,restoredefaults,persist | Bindings unit + real input adapter GUI test |
| A2 | Visual subtitles shade spawn+edge arrow,windwarning,last10s,lowfuel | Mute/no-audio framebuffers + GUI assertions |
| A3 | Reduced motion,UI font>=18px at720p,large1.25 | Renderer telemetry/font tests + visual QA |
| P1 | Clone/build/play<=3commands,executable perplatform | Clean source install + packaged executable smoke in CI |
| P2 | README/fullchangelog/credits/license,retro1–2pages | Local link/artifact review |
| P3 | DemoMP4<5min, gameplay/test/headless/bench | Live GUI framebuffer recording, actual command logs; disclose automated inputs |
| R1 | Contract1.3,bench_cmd/soak_cmd, v1.0–1.2 unreplaced regressions | Full gate and CI; byte-identical fixture comparison across phase3 source |

Đo RSS bằng psutil (bytes/1024²). P95 dùng nội suy tuyến tính type7;1%low đúng
k=ceil(.01N),trung bìnhkdt lớn nhất. Soak indexi=0…n−1, seedbase+i, RNGinput
riêng cùngseed; mem_end sau khi bỏ state cuối/gc/reset Game cuối về đầuĐêm.
Các lựa chọn chưa nêu chi tiết sẽ được ghi trong notes/ADR thay vì đoán ẩn.
