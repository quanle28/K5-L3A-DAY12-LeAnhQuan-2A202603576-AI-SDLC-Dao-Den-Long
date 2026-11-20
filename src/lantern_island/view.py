"""Pygame desktop game: campaign, menus, audio and shared 60Hz simulation."""
import math
import time
from .pygame_canvas import pg,PygameCanvas
from .render import Scene
from .maps import PALETTE,World
from .model import Game,DEFAULT_INPUT,DT
from .campaign import Campaign,Settings
from .audio import Audio


class App:
    def __init__(self,seed=12,settings_path=None,size=(1280,720),audio=True):
        pg.display.init(); pg.font.init()
        self.surface=pg.display.set_mode(size,pg.RESIZABLE)
        pg.display.set_caption('Đảo Đèn Lồng · Ba hòn đảo')
        self.canvas=PygameCanvas(self.surface); self.scene=Scene(self.canvas)
        self.settings=Settings(settings_path)
        self.audio=Audio(pg,self.settings.volume) if audio else None
        self.seed=seed; self.campaign=Campaign(); self.game=Game(seed)
        self.screen='menu'; self.settings_return='menu'; self.running=True
        self.yaw=0.; self.keys=set(); self.buttons=[]; self.message=''
        self.message_until=0; self.last_countdown=None; self.accumulator=0.

    def start_night(self,night=None,playing=False):
        if night: self.campaign.night=night
        self.game=Game(self.seed,night=self.campaign.night)
        self.yaw=0.; self.keys.clear(); self.message=''; self.last_countdown=None
        self.screen='playing' if playing else 'intro'
        if self.audio:
            self.audio.pause(False); self.audio.start(self.game.night)

    def resume(self):
        if self.game.state=='paused':
            self.game.step(dict(DEFAULT_INPUT))
            self.game.step(dict(DEFAULT_INPUT,pause=True))
        self.keys.clear(); self.screen='playing'
        if self.audio: self.audio.pause(False)

    def pause(self):
        if self.game.state=='playing':
            self.game.previous['pause']=False
            self.game.step(dict(DEFAULT_INPUT,pause=True))
        self.keys.clear(); self.screen='pause'
        if self.audio: self.audio.pause(True)

    def act(self,action):
        if action=='new': self.campaign=Campaign(); self.start_night()
        elif action=='play': self.screen='playing'; self.keys.clear()
        elif action=='resume': self.resume()
        elif action=='retry': self.start_night(playing=True)
        elif action=='next':
            if self.campaign.next(): self.start_night()
            else: self.screen='dawn'
        elif action=='settings':
            self.settings_return=self.screen; self.screen='settings'
        elif action=='back':
            self.settings.save(); self.screen=self.settings_return
        elif action=='menu':
            self.screen='menu'; self.keys.clear()
            if self.audio: self.audio.pause(False)
        elif action=='quit': self.running=False

    def handle_event(self,event):
        if event.type==pg.QUIT: self.running=False
        elif event.type==pg.VIDEORESIZE:
            self.surface=pg.display.set_mode((max(960,event.w),max(600,event.h)),pg.RESIZABLE)
            self.canvas.surface=self.surface
        elif event.type==pg.WINDOWFOCUSLOST and self.screen=='playing': self.pause()
        elif event.type==pg.KEYUP: self.keys.discard(event.key)
        elif event.type==pg.KEYDOWN:
            if event.key in self.keys: return
            self.keys.add(event.key)
            if self.screen=='playing':
                if event.key in (pg.K_ESCAPE,pg.K_p): self.pause()
                elif event.key==pg.K_r: self.start_night(playing=True)
            elif self.screen=='pause' and event.key in (pg.K_ESCAPE,pg.K_p): self.resume()
            elif self.screen=='settings':
                if event.key==pg.K_ESCAPE: self.act('back')
                elif event.key in (pg.K_LEFT,pg.K_RIGHT):
                    self.settings.volume=max(0,min(1,self.settings.volume+(.05 if event.key==pg.K_RIGHT else -.05)))
                    self.settings.save()
                    if self.audio: self.audio.volume(self.settings.volume)
                elif event.key in (pg.K_UP,pg.K_DOWN):
                    self.settings.sensitivity=max(.05,min(1,self.settings.sensitivity+(.05 if event.key==pg.K_UP else -.05)))
                    self.settings.save()
            elif event.key==pg.K_RETURN:
                self.act({'menu':'new','intro':'play','result':'next' if self.game.state=='won' else 'retry','dawn':'menu'}.get(self.screen,'menu'))
            elif event.key==pg.K_ESCAPE:
                self.act('quit' if self.screen=='menu' else 'menu')
        elif event.type==pg.MOUSEMOTION and self.screen=='playing' and event.buttons[2]:
            self.yaw+=event.rel[0]*self.settings.sensitivity
        elif event.type==pg.MOUSEBUTTONDOWN and event.button==1:
            if self.screen=='settings':
                w,h=self.surface.get_size(); x,y=event.pos
                if w/2-180<=x<=w/2+180:
                    if abs(y-(h/2-25))<20:
                        self.settings.volume=max(0,min(1,(x-(w/2-180))/360))
                        if self.audio: self.audio.volume(self.settings.volume)
                        self.settings.save(); return
                    if abs(y-(h/2+60))<20:
                        self.settings.sensitivity=.05+.95*max(0,min(1,(x-(w/2-180))/360))
                        self.settings.save(); return
            for rect,action in self.buttons:
                if rect.collidepoint(event.pos): self.act(action); break

    def controls(self):
        k=self.keys
        self.yaw+=(int(pg.K_c in k)-int(pg.K_q in k))*1.5
        return dict(DEFAULT_INPUT,move=[int(pg.K_d in k or pg.K_RIGHT in k)-int(pg.K_a in k or pg.K_LEFT in k),
                                       int(pg.K_w in k or pg.K_UP in k)-int(pg.K_s in k or pg.K_DOWN in k)],
                    cam_yaw_deg=self.yaw,jump=pg.K_SPACE in k,interact=pg.K_e in k,pulse=pg.K_f in k,
                    dash=pg.K_LSHIFT in k or pg.K_RSHIFT in k)

    def step_once(self,c=None):
        if self.screen in ('pause','settings') and self.game.state=='paused':
            self.game.step(dict(DEFAULT_INPUT)); return []
        if self.screen!='playing': return []
        c=self.controls() if c is None else c
        jump=c.get('jump',False) and not self.game.previous.get('jump',False) and self.game.grounded
        events=self.game.step(c)
        if jump and self.audio: self.audio.play('jump')
        for event in events:
            name=event['name']
            if self.audio: self.audio.play(name)
            if name=='lantern_lit': self.message='Một ngọn đèn đã thức giấc. Vùng sáng giữ Mây an toàn.'
            elif name=='player_hit': self.message='Mây mất một Ngọn Lửa. Hãy tìm vùng sáng!'
            elif name=='drifter_steal': self.message='Gió Lạc đã cướp ánh sáng — dùng F để lấy lại!'
            else: continue
            self.message_until=self.game.sim_tick+150
        if self.game.sim_tick>self.message_until: self.message=''
        seconds=math.ceil(self.game.time_left)
        if 0<seconds<=10 and seconds!=self.last_countdown:
            if self.audio: self.audio.play('countdown')
            self.last_countdown=seconds
        if self.game.night==3 and self.game.wind_enabled and self.game.sim_tick%1800==1680:
            if self.audio: self.audio.play('wind')
        if self.game.state in ('won','lost'):
            self.campaign.complete(self.game); self.screen='result'; self.keys.clear()
            if self.audio: self.audio.play(self.game.state)
        return events

    def button(self,y,text,action):
        w,h=self.surface.get_size(); c=self.canvas; p=PALETTE
        rect=pg.Rect(w/2-175,y-22,350,44)
        hover=rect.collidepoint(pg.mouse.get_pos())
        c.create_rectangle(*rect.topleft,*rect.bottomright,fill=p['cloud'] if hover else p['fog'],outline=p['gold'])
        c.create_text(w/2,y,text=text,fill=p['text'],font=('Segoe UI',13,'bold'))
        self.buttons.append((rect,action))

    def draw(self):
        w,h=self.surface.get_size(); self.buttons=[]; c=self.canvas; p=PALETTE
        self.scene.draw(self.game,self.yaw,w,h,self.message,total_score=self.campaign.total)
        if self.screen=='playing': return
        overlay=pg.Surface((w,h),pg.SRCALPHA); overlay.fill((14,20,48,190)); self.surface.blit(overlay,(0,0))
        c.create_rectangle(w/2-315,h/2-235,w/2+315,h/2+240,fill=p['sky'],outline=p['gold'],width=2)
        title={'menu':'ĐẢO ĐÈN LỒNG','intro':'ĐÊM %d · %s'%(self.game.night,World.names[self.game.night]),
               'pause':'ĐÊM ĐANG NGHỈ','settings':'CÀI ĐẶT','result':'ĐẢO ĐÃ SÁNG LẠI' if self.game.state=='won' else 'THỬ LẠI, MÂY NHÉ','dawn':'BÌNH MINH'}.get(self.screen,'')
        c.create_text(w/2,h/2-180,text=title,fill=p['gold'],font=('Segoe UI',24,'bold'))
        if self.screen=='menu':
            c.create_text(w/2,h/2-105,text='Ba hòn đảo, một lời hẹn mang ánh sáng trở về.\nMây cùng chiếc nón lá và ngọn đèn nhỏ đang chờ bạn.',fill=p['text'],font=('Segoe UI',13))
            for dy,text,act in [(0,'Bắt đầu · ENTER','new'),(60,'Cài đặt','settings'),(120,'Thoát','quit')]: self.button(h/2+dy,text,act)
        elif self.screen=='intro':
            story={1:'Ông Đăng: “Đừng sợ đêm. Mỗi đốm sáng là một đường về.”',
                   2:'Ông Đăng: “Qua cầu tre, nhớ nghe tiếng gió lạc.”',
                   3:'Ông Đăng: “Lên tháp chuông, ta sẽ thấy bình minh.”'}[self.game.night]
            hint={1:'Giữ chuột phải / Q,C xoay camera; SHIFT lướt.',2:'Đi qua cầu tre hoặc chạm bục vàng để bay sang đảo kia.',3:'Theo hai dốc lên tầng một; bục vàng đưa Mây lên tầng chuông.'}[self.game.night]
            c.create_text(w/2,h/2-80,text=story+'\n\nThắp %d đèn trong %d giây. Giữ lại ba Ngọn Lửa.\n\n'%(len(self.game.lanterns),self.game.duration)+hint,fill=p['text'],font=('Segoe UI',12))
            self.button(h/2+55,'Vào Đêm · ENTER','play'); self.button(h/2+115,'Về menu','menu')
        elif self.screen=='pause':
            for i,(text,act) in enumerate([('Tiếp tục · P / ESC','resume'),('Chơi lại Đêm','retry'),('Cài đặt','settings'),('Về menu','menu')]): self.button(h/2-70+i*60,text,act)
        elif self.screen=='settings':
            for y,label,value in [(h/2-25,'Âm lượng',self.settings.volume),(h/2+60,'Độ nhạy chuột',(self.settings.sensitivity-.05)/.95)]:
                c.create_text(w/2,y-30,text=label+' · %.2f'%(self.settings.volume if label=='Âm lượng' else self.settings.sensitivity),fill=p['text'],font=('Segoe UI',13))
                c.create_rectangle(w/2-180,y-4,w/2+180,y+4,fill=p['fog'],outline=p['gold'])
                xx=w/2-180+360*value; c.create_oval(xx-9,y-9,xx+9,y+9,fill=p['gold'],outline='')
            c.create_text(w/2,h/2+105,text='Giữ chuột phải để xoay camera · Cài đặt được lưu tự động',fill=p['text'],font=('Segoe UI',10))
            self.button(h/2+165,'Quay lại · ESC','back')
        elif self.screen=='result':
            c.create_text(w/2,h/2-95,text='Điểm Đêm: %d\nTổng các Đêm đã thắng: %d'%(self.game.score,self.campaign.total),fill=p['text'],font=('Segoe UI',16))
            self.button(h/2+15,'Đêm tiếp theo · ENTER' if self.game.state=='won' and self.game.night<3 else ('Đón Bình Minh · ENTER' if self.game.state=='won' else 'Chơi lại Đêm · ENTER'),'next' if self.game.state=='won' else 'retry')
            self.button(h/2+80,'Về menu','menu')
        elif self.screen=='dawn':
            c.create_text(w/2,h/2-50,text='Ba hòn đảo đã tìm lại ánh sáng.\n\nTổng điểm: %d\nCảm ơn bạn đã giữ đèn cùng Mây.'%self.campaign.total,fill=p['core'],font=('Segoe UI',17))
            self.button(h/2+110,'Về menu · ENTER','menu')

    def run(self):
        clock=pg.time.Clock()
        while self.running:
            elapsed=min(clock.tick(60)/1000,.25); self.accumulator+=elapsed
            for event in pg.event.get(): self.handle_event(event)
            while self.accumulator>=DT:
                self.step_once(); self.accumulator-=DT
            self.draw(); pg.display.flip()
        pg.quit()


def play(seed=12):
    App(seed).run()
