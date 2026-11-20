# Ticket-03 — Đèn cạn dầu / Contract v1.2

Nguồn: bản Ticket-03 đầy đủ người dùng dán trong hội thoại. Tag bàn giao phase-3.
ADR trước triển khai: [0003-fuel-and-dawn](../adr/0003-fuel-and-dawn.md).

| ID | Tiêu chí nghiệm thu | Bằng chứng dự kiến |
|---|---|---|
| F1 | Max100, thắp mới/lại100, tự hao1/s, không sai số tích lũy | test6000step/rounding, fuel-decay scenario |
| F2 | Refuel ceilđúng; fullskip; receiving nearest/ID; +5/mote | refuel/full/tie unit tests và refuel scenario |
| F3 | Out resetdep0/evertrue; relight5/relit_count; firstcost10 | relight/last-tick scenarios |
| S1 | Fuel30 cósafe, <30mất; refuel≥30eject≤30step/nohit | boundary/refuel-eject scenarios |
| S2 | Chỉ wander tìm weaknearest/tieID; chase không đổi; fallbackunlit | weak-target/chase tests |
| S3 | Drain≤2,5/s/shade cộng dồn cùngdecay, event60simstep | drain-stack/drain-pause scenarios |
| S4 | Drain→chase≤6, out/refuel/distance→wander, pulse→stun, tỉnh→wander | transition/pulse tests |
| W1 | 240/270/300s; không earlywin; dawngưỡng3/5,4/6,5/7; no_flamesưu tiên | all-lit-running, dawn-n1/n2/n3, expiry/refill/death-at-dawn |
| C1 | Capacity10+2successful_lights cap20, relighttính, setupkhôngtính/resetĐêm | capacity/setup/pickup-next-step tests |
| P1 | +5/mote,+100first,+40relight,+5normal/+15drainpulse; dawn50+floorfuel mỗiđèn và50/flame; nobonustime | score formula tests |
| U1 | Fuelbar trên đèn, low<30blink1Hz; HUDcarried/capacity | GUI framebuffers on/off, HUD smoke |
| U2 | Colorblind saved; shadeoutline/eyesblue, dangerwhite+⚠; tắt xẹp20%/rách | Settings tests, GUI mode frames/model unchanged |
| T1 | Contract1.2/new tuning, lampfuel1decimal/ever_lit/relit_count, capacity, drainstate/targetscenario/newevents/reason | CLI/schema tests + deterministic replay |
| R1 | Giữ mọi hành vi v1.1 không bị thay, không skipâmthầm | migrated58tests + changelog/retro |

Thứ tự: giữ12bước Ticket-02, thêmfuel/aggregate drain ởstep2 rồi out ngay sau;
interactstep5 có thểrelight đènvừaout; safe6/pulse7/AI8/contact9/spawn10/
terminal11. Pausedwalltick vẫn tăng, sim_tick và tất cả dầu/drain/counters đông.

Các quyết định cho chỗ chưa nêu chi tiết được ghi trong ADR. Chỉ xuất1decimal,
threshold luôn dùngunitschínhxác, khôngdùngfuel đãlàmtròn. Cài đặt accessibility
khôngthamgia môhình/RNG/headless. Ticket04chưacó, không tạoReleasev1.0.0.
