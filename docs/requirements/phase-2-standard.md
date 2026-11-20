# Ticket-02 đầy đủ — baseline thực thi

Nguồn: người dùng dán toàn bộ "Ba hòn đảo" trong hội thoại, gồm bảng số liệu
và RGB đã thiếu trước đó. Nội dung này thay trạng thái thiếu bảng ở bản chuẩn bị.

- 60Hz; run6; jump7/gravity-20; dash14/12tick/CD90, hướng move hoặc facing,
  trên không khóa độ cao, không bất tử. Charm run7.2, dash không CD.
- Capacity10; pickupXZ1/chênhY1.5; initial20 điểm khác nhau; cap30;
  mote sinh tick240k tại điểm trống. Depositcost10/radius2, partial/nearest/ID.
- Safe6; shade ở trong lúc sáng bị đẩy ra trong≤30tick, miễn gây hit lúc đẩy.
- Pulsecost3/radius3D5 từ foot+.8/CD180; stun120; push4 trong15tick, refresh.
- Shade4 (night3:4.5); detect12/forget18; hitXZ1/dY1.5; recoil2 trong60tick.
  Spawn2 tại300 rồi1 mỗi480/420/360tick, cap6/8/10, cách Mây≥15.
- Hit -1flame/dropfloor(carried/2), vòng1.5…2.5, TTL480, invuln90.
  FallY<-10 bỏ qua invuln, -1flame/mất hết đồ, wait60 rồi spawn/v0/invuln90.
- Flames3 mỗi đêm, duration300/330/360. Terminal: no_flames > all_lit > dawn.
- Score10/mote NẠP,100/lit,5/shade pulse; win floor(seconds)*2+50*flames.
  Campaign chỉ cộng điểm những đêm thắng.
- Tick order: pause → giảm counters → move/fall → pickup → deposit → safe
  → pulse → shade/drifter move → drifter steal rồi shade hit ID tăng → spawn
  → terminal → snapshot. Pause đóng băng sim_tick/counter, wall tick vẫn tăng.
- Maps và acceptance criteria: phase-2.md; tọa độ runtime tại maps.py.
- Drifter night2/3, spawn1200k cap2; idle2/chase7 nếucarried≥5,d≤15;
  contactXZ1.2 stealmin3, flee240; pulsechase→flee0, pulseflee mangđồ→drop,
  flee còn120. Safe/invuln không ngăn cướp.
- Charm600tick, refresh, respawn2700; C1night2(35,0,0), night3C1/C2(±30,0,25).
- Windnight3: warning28s mỗi30s, active30…35s,dir seededrandom,push2.
- Contract1.1: night1/2/3, pause/dash edges; fields/events mới đúng Ticket-02.
- GUI: campaign/menu/intro/results/dawn, pause4options, volume/sensitivity
  persistent, nhạc/SFX, HUD10ô/cooldown/E/offscreenarrow,≥30FPS1280×720.

RGB (nguồn chính xác): trời#0E1430,sương#1B2350,cỏ#2F5D50,cát#C9B48A,
gỗ#6B4A2F,biểnmây#12384A,đènsáng#FFB347,lõi#FFE9B0,tắt#5B5F6E,
motecore#FFF6C2/halo#FFE58A,shade#120A1A/viền#7A3CFF/stun#3A3450,
áo#E8E2D0,khăn/charm#C8102E,gold/score#F2C14E,drifter#8FA3B8,
danger#FF5A5F,text#F5F1E6. Ambient=.15+.55*lit/count.
