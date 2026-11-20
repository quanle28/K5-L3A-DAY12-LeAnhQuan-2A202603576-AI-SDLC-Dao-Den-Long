"""Capture the live game framebuffer, with disclosed automated keys and actual logs.

Development-only encoder: pip install --target .builddeps imageio-ffmpeg==0.6.0
The video is not a human playtest or a full unmodified three-Night victory.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'.builddeps'))
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from src.lantern_island.view import App,pg
from src.lantern_island.model import Game,DEFAULT_INPUT
from src.lantern_island.performance import benchmark_game,benchmark_step,orbit_camera
import imageio_ffmpeg

def main():
    target=ROOT/'docs/demo'; target.mkdir(parents=True,exist_ok=True)
    proof=ROOT/'docs/proof/phase-4'; proof.mkdir(parents=True,exist_ok=True)
    test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=ROOT,capture_output=True,text=True)
    assert test.returncode==0,test.stderr
    (proof/'demo-tests.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
    with tempfile.TemporaryDirectory() as temp:
        headless=Path(temp)/'run.jsonl'
        command=[sys.executable,'game.py','--headless','--seed','12','--night','1','--scenario','tests/scenarios/v12/dawn-relight.json','--inputs','tests/scenarios/v12/dawn-relight.inputs.json','--ticks','1','--out',str(headless)]
        subprocess.run(command,cwd=ROOT,check=True)
        actual_lines=headless.read_text(encoding='utf-8').splitlines()
        (proof/'demo-headless.jsonl').write_text('\n'.join(actual_lines)+'\n',encoding='utf-8')
        app=App(settings_path=Path(temp)/'settings.json',audio=False)
        encoder=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-',
                                  '-an','-vcodec','libx264','-preset','veryfast','-crf','27','-pix_fmt','yuv420p','-movflags','+faststart',str(target/'demo.mp4')],
                                 stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=(target/'encoder.log').open('w'),
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        clock=pg.time.Clock(); bench=None; started=time.perf_counter()
        def key(code,on): app.handle_event(pg.event.Event(pg.KEYDOWN if on else pg.KEYUP,key=code))
        try:
            for frame in range(72*30):
                t=frame/30; caption=''; detail=''
                pg.event.pump()
                if frame==60: app.act('new')
                if frame==90: app.act('play'); key(pg.K_w,True)
                if frame==150: key(pg.K_SPACE,True)
                if frame==151: key(pg.K_SPACE,False)
                if frame==210: key(pg.K_LSHIFT,True)
                if frame==211: key(pg.K_LSHIFT,False)
                if frame==270: key(pg.K_w,False)
                if frame==330:
                    app.start_night(1,playing=True)
                    app.game=Game(12,dict(random_motes=False,random_shades=False,random_drifters=False,
                                         motes=[[0,0,3]]*10+[[0,0,4]]*6,
                                         lanterns=[dict(id='L1',pos=[0,0,5])],
                                         shades=[dict(pos=[0,.8,8],state='stunned',state_ticks_left=1000)]))
                    key(pg.K_w,True)
                if frame==351: key(pg.K_w,False)
                if frame in (360,540): key(pg.K_e,True)
                if frame in (361,541): key(pg.K_e,False)
                if frame==450: key(pg.K_f,True)
                if frame==451: key(pg.K_f,False)
                if frame==600: app.pause(); app.act('settings')
                if frame==630: app.act('large_text'); app.act('reduced_motion'); app.act('colorblind')
                if frame==690: app.act('bindings'); app.act('bind:jump'); key(pg.K_w,True)
                if frame==750: key(pg.K_u,True)
                if frame==810: app.act('bindings-default'); app.act('bindings-back'); app.act('back'); app.resume()
                if frame==840:
                    app.game.flames=0; app.step_once(); app.name_text='Quan_Demo'
                if frame==900: app.act('submit-score'); app.act('leaderboard')
                if frame==960: app.start_night(2,playing=True); app.settings.large_text=False
                if frame==1050: app.start_night(3,playing=True)
                if frame==1680: bench=benchmark_game(42)
                if 3<=t<11 or 11<=t<20 or 27<=t<28 or 32<=t<36:
                    for _ in range(2): app.step_once()
                if t<36:
                    app.draw()
                    if t<3: caption='ĐẢO ĐÈN LỒNG · v1.0.0'; detail='Video từ cửa sổ game thật · phím tự động · không phải chơi tay'
                    elif t<11: caption='CHƠI TRÊN MAP CHUẨN'; detail='60 tick/s · di chuyển, nhảy, lướt qua input adapter thật'
                    elif t<20: caption='FIXTURE MINH HỌA (đặt gần đèn)'; detail='Nhặt → thắp → sức chứa12 → Tỏa Sáng → châm dầu; không phải lượt thắng map chuẩn'
                    elif t<23: caption='DỄ TIẾP CẬN'; detail='Chữ lớn ×1.25 · giảm chuyển động · bảng màu được lưu'
                    elif t<27: caption='ĐỔI PHÍM'; detail='W bị báo trùng → đổi Nhảy sang U → khôi phục mặc định'
                    elif t<32: caption='LƯU ĐIỂM KHI THUA (fixture)'; detail='Tổng chỉ tính các Đêm thắng; tên và bảng điểm lưu trên đĩa'
                    else: caption='XEM BẢN ĐỒ ĐÊM2 / ĐÊM3'; detail='Chuyển trực tiếp để demo; trong campaign phải thắng Đêm trước'
                elif t<56:
                    app.surface.fill('#0E1430'); c=app.canvas
                    if t<45:
                        caption='TEST THẬT · ĐẦU RA VỪA CHẠY'; detail='python -m unittest discover -s tests -q'
                        lines=(test.stdout+test.stderr).strip().splitlines()[-8:]
                    else:
                        caption='HEADLESS THẬT · FIXTURE dawn-relight'; detail='python game.py --headless ... --ticks 1 --out run.jsonl'
                        lines=[line for line in actual_lines if '"event"' in line or '"end"' in line]
                    c.create_text(50,320,anchor='w',text='\n'.join(lines),fill='#F5F1E6',font=('Segoe UI',17),width=1180)
                elif t<65:
                    for _ in range(2): benchmark_step(bench)
                    app.canvas.text_scale=1
                    app.scene.draw(bench,0,1280,720,camera=orbit_camera(t-56),benchmark=True)
                    measured=json.loads((ROOT/'bench.json').read_text())
                    caption='CẢNH BENCH CHUẨN · 200 BÓNG / 100 ĐOM ĐÓM'
                    detail='Số đo30s riêng (không encoder): avg %.1f · 1%%low %.1f · load %.0fms'%(measured['avg_fps'],measured['p1_low_fps'],measured['load_ms'])
                else:
                    app.surface.fill('#0E1430'); c=app.canvas
                    measured=json.loads((ROOT/'soak.json').read_text())
                    caption='SOAK10 ĐÊM · CÙNG MỘT TIẾN TRÌNH'; detail='Bằng chứng lưu: bench.json, raw dt, soak.json, docs/proof/phase-4'
                    c.create_text(640,330,text='crashes: %d\nRSS: %.2f → %.2f MiB\nKết quả10lượt: %s\n\nTag phase-1 → phase-4 · Release v1.0.0'%(measured['crashes'],measured['mem_start_mb'],measured['mem_end_mb'],', '.join(measured['results'])),fill='#F5F1E6',font=('Segoe UI',18),width=1100)
                overlay=pg.Surface((1280,84)); overlay.fill('#1B2350'); app.surface.blit(overlay,(0,0))
                app.canvas.create_text(640,24,text=caption,fill='#F2C14E',font=('Segoe UI',18,'bold'))
                app.canvas.create_text(640,59,text=detail,fill='#F5F1E6',font=('Segoe UI',14),width=1240)
                pg.display.flip()
                if frame in (390,660,720,990,1080,1260,1500,1770,2040): pg.image.save(app.surface,str(target/('frame-%04d.png'%frame)))
                encoder.stdin.write(pg.image.tobytes(app.surface,'RGB'))
                clock.tick(30)
            encoder.stdin.close(); assert encoder.wait(timeout=60)==0
        finally:
            pg.quit()
            if encoder.poll() is None: encoder.kill()
        reader=imageio_ffmpeg.read_frames(str(target/'demo.mp4')); metadata=next(reader); reader.close()
        assert metadata['duration']<300 and metadata['size']==(1280,720)
        metadata.update(wall_seconds=time.perf_counter()-started,frames=2160,automated_input=True,audio='silent; captions; dummy audio not a listening test',
                        limitations='Live window framebuffer with scripted keys, declared controlled fixture and direct map previews; actual captured command output. Not a human playtest or a full three-Night victory.')
        (target/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Recorded and validated72second MP4: docs/demo/demo.mp4')

if __name__=='__main__': main()
