"""Release desktop UI: local scores, remapping, accessible notices and shared gameplay."""
from datetime import timedelta,timezone
import math
import unicodedata
from .pygame_canvas import pg,PygameCanvas
from .render import Scene
from .maps import PALETTE,World
from .model import Game,DEFAULT_INPUT,DT
from .campaign import Campaign,Settings,ACTION_LABELS,DEFAULT_BINDINGS
from .leaderboard import Leaderboard,timestamp
from .audio import Audio


class App:
    def __init__(self,seed=12,settings_path=None,size=(1280,720),audio=True):
        pg.display.init(); pg.font.init()
        self.surface=pg.display.set_mode(size,pg.RESIZABLE,vsync=0)
        pg.display.set_caption('Đảo Đèn Lồng · Bình minh v1.0.0')
        self.canvas=PygameCanvas(self.surface); self.scene=Scene(self.canvas)
        self.settings=Settings(settings_path)
        self.board=Leaderboard(self.settings.path.with_name('leaderboard.json'))
        self.board_entries=[]; self.name_text=''; self.name_error=''; self.score_after='result'; self.score_saved=False
        self.pending_binding=None; self.binding_message=''; self.binding_codes={}; self._load_bindings()
        self.audio=Audio(pg,self.settings.volume) if audio else None
        self.seed=seed; self.campaign=Campaign(); self.game=Game(seed)
        self.screen='menu'; self.settings_return='menu'; self.running=True
        self.yaw=0.; self.keys=set(); self.buttons=[]; self.message=''
        self.message_until=0; self.last_countdown=None; self.accumulator=0.; self.notices=[]

    def _load_bindings(self):
        try: self.binding_codes={a:[pg.key.key_code(k) for k in keys] for a,keys in self.settings.bindings.items()}
        except ValueError:
            self.settings.bindings={k:list(v) for k,v in DEFAULT_BINDINGS.items()}
            self.binding_codes={a:[pg.key.key_code(k) for k in keys] for a,keys in self.settings.bindings.items()}
            self.binding_message='Phím lưu không hợp lệ; đang dùng mặc định.'

    def down(self,action): return any(key in self.keys for key in self.binding_codes[action])

    def start_night(self,night=None,playing=False):
        if night: self.campaign.night=night
        self.game=Game(self.seed,night=self.campaign.night)
        self.yaw=0.; self.keys.clear(); self.message=''; self.last_countdown=None; self.notices=[]; self.score_saved=False
        self.screen='playing' if playing else 'intro'
        pg.key.stop_text_input()
        if self.audio: self.audio.pause(False); self.audio.start(self.game.night)

    def resume(self):
        if self.game.state=='paused':
            self.game.step(dict(DEFAULT_INPUT)); self.game.step(dict(DEFAULT_INPUT,pause=True))
        self.keys.clear(); self.screen='playing'
        if self.audio: self.audio.pause(False)

    def pause(self):
        if self.game.state=='playing':
            self.game.previous['pause']=False; self.game.step(dict(DEFAULT_INPUT,pause=True))
        self.keys.clear(); self.screen='pause'
        if self.audio: self.audio.pause(True)

    def open_score(self,after):
        self.score_after=after; self.name_text=''; self.name_error=''; self.screen='score-entry'; self.keys.clear()
        pg.key.start_text_input()

    def act(self,action):
        if action=='new': self.campaign=Campaign(); self.start_night()
        elif action=='play': self.screen='playing'; self.keys.clear()
        elif action=='resume': self.resume()
        elif action=='retry': self.start_night(playing=True)
        elif action=='next':
            if self.campaign.next(): self.start_night()
            else: self.screen='dawn'
        elif action=='settings': self.settings_return=self.screen; self.screen='settings'
        elif action in ('colorblind','reduced_motion','large_text'):
            setattr(self.settings,action,not getattr(self.settings,action)); self.settings.save()
        elif action=='bindings': self.screen='bindings'; self.pending_binding=None; self.binding_message=''
        elif action.startswith('bind:'): self.pending_binding=action.split(':',1)[1]; self.binding_message='Nhấn phím mới; có thể bấm Quay lại để hủy.'
        elif action=='bindings-default':
            self.settings.restore_bindings(); self._load_bindings(); self.pending_binding=None; self.binding_message='Đã khôi phục mặc định.'
        elif action=='bindings-back': self.screen='settings'; self.pending_binding=None
        elif action=='back': self.settings.save(); self.screen=self.settings_return
        elif action=='leaderboard': self.board_entries=self.board.entries(); self.screen='leaderboard'
        elif action=='score': self.open_score('leaderboard')
        elif action=='submit-score':
            try:
                if not self.score_saved:
                    self.board.add(self.name_text,self.campaign.total,len(self.campaign.scores),self.seed)
                    self.score_saved=True
                pg.key.stop_text_input()
                self.act('leaderboard') if self.score_after=='leaderboard' else setattr(self,'screen',self.score_after)
            except (ValueError,OSError) as error: self.name_error=str(error)
        elif action=='skip-score':
            pg.key.stop_text_input(); self.screen=self.score_after
            if self.screen=='leaderboard': self.board_entries=self.board.entries()
        elif action=='menu':
            self.screen='menu'; self.keys.clear(); pg.key.stop_text_input()
            if self.audio: self.audio.pause(False)
        elif action=='quit': self.running=False

    def handle_event(self,event):
        if event.type==pg.QUIT: self.running=False
        elif event.type==pg.VIDEORESIZE:
            self.surface=pg.display.set_mode((max(960,event.w),max(600,event.h)),pg.RESIZABLE,vsync=0); self.canvas.surface=self.surface
        elif event.type==pg.WINDOWFOCUSLOST and self.screen=='playing': self.pause()
        elif event.type==pg.TEXTINPUT and self.screen=='score-entry':
            self.name_text=unicodedata.normalize('NFC',self.name_text+event.text)[:12]; self.name_error=''
        elif event.type==pg.KEYUP: self.keys.discard(event.key)
        elif event.type==pg.KEYDOWN:
            if self.screen=='score-entry':
                if event.key==pg.K_BACKSPACE: self.name_text=self.name_text[:-1]
                elif event.key==pg.K_RETURN: self.act('submit-score')
                elif event.key==pg.K_ESCAPE: self.act('skip-score')
                return
            if self.screen=='bindings' and self.pending_binding:
                try:
                    key=pg.key.name(event.key); pg.key.key_code(key)
                    self.settings.rebind(self.pending_binding,key); self._load_bindings()
                    self.binding_message='Đã đổi %s thành %s'%(ACTION_LABELS[self.pending_binding],key.upper()); self.pending_binding=None
                except ValueError as error: self.binding_message=str(error)
                return
            if event.key in self.keys: return
            self.keys.add(event.key)
            if self.screen=='playing':
                if event.key in self.binding_codes['pause']: self.pause()
            elif self.screen=='pause' and event.key in self.binding_codes['pause']: self.resume()
            elif self.screen=='bindings' and event.key==pg.K_ESCAPE: self.act('bindings-back')
            elif self.screen=='settings':
                if event.key==pg.K_ESCAPE: self.act('back')
                elif event.key in (pg.K_LEFT,pg.K_RIGHT):
                    self.settings.volume=max(0,min(1,self.settings.volume+(.05 if event.key==pg.K_RIGHT else -.05))); self.settings.save()
                    if self.audio: self.audio.volume(self.settings.volume)
                elif event.key in (pg.K_UP,pg.K_DOWN):
                    self.settings.sensitivity=max(.05,min(1,self.settings.sensitivity+(.05 if event.key==pg.K_UP else -.05))); self.settings.save()
            elif event.key==pg.K_RETURN:
                self.act({'menu':'new','intro':'play','result':'next' if self.game.state=='won' else 'retry','dawn':'score','leaderboard':'menu'}.get(self.screen,'menu'))
            elif event.key==pg.K_ESCAPE: self.act('quit' if self.screen=='menu' else 'menu')
        elif event.type==pg.MOUSEMOTION and self.screen=='playing' and event.buttons[2]: self.yaw+=event.rel[0]*self.settings.sensitivity
        elif event.type==pg.MOUSEBUTTONDOWN and event.button==1:
            if self.screen=='settings':
                w,h=self.surface.get_size(); x,y=event.pos
                if w/2-180<=x<=w/2+180:
                    if abs(y-(h/2-130))<18:
                        self.settings.volume=max(0,min(1,(x-(w/2-180))/360)); self.settings.save()
                        if self.audio: self.audio.volume(self.settings.volume)
                        return
                    if abs(y-(h/2-60))<18:
                        self.settings.sensitivity=.05+.95*max(0,min(1,(x-(w/2-180))/360)); self.settings.save(); return
            for rect,action in self.buttons:
                if rect.collidepoint(event.pos): self.act(action); break

    def controls(self):
        bound={key for keys in self.binding_codes.values() for key in keys}
        self.yaw+=(int(pg.K_c in self.keys and pg.K_c not in bound)-int(pg.K_q in self.keys and pg.K_q not in bound))*1.5
        return dict(DEFAULT_INPUT,move=[int(self.down('move_right'))-int(self.down('move_left')),int(self.down('move_up'))-int(self.down('move_down'))],
                    cam_yaw_deg=self.yaw,jump=self.down('jump'),interact=self.down('interact'),pulse=self.down('pulse'),dash=self.down('dash'))

    def step_once(self,c=None):
        if self.game.state=='paused' and self.screen in ('pause','settings','bindings'):
            self.game.step(dict(DEFAULT_INPUT)); return []
        if self.screen!='playing': return []
        c=self.controls() if c is None else c
        jump=c.get('jump',False) and not self.game.previous.get('jump',False) and self.game.grounded
        events=self.game.step(c)
        if jump and self.audio: self.audio.play('jump')
        for event in events:
            name=event['name']
            if self.audio: self.audio.play(name)
            if name=='shade_spawned':
                shade=next(s for s in self.game.shades if s['id']==event['data']['id'])
                self.notices.append(dict(kind='shade',pos=list(shade['pos']),until=self.game.sim_tick+180))
            if name=='lantern_lit': self.message='Một ngọn đèn đã thức giấc. Hãy giữ dầu tới bình minh.'
            elif name=='lantern_out': self.message=event['data']['lantern_id']+' cạn dầu — thắp lại cần5đom đóm.'
            elif name=='refuel': self.message='Đã châm dầu cho '+event['data']['lantern_id']
            elif name=='player_hit': self.message='Mây mất một Ngọn Lửa. Hãy tìm vùng sáng!'
            elif name=='drifter_steal': self.message='Gió Lạc đã cướp ánh sáng — dùng Tỏa Sáng để lấy lại!'
            else: continue
            self.message_until=self.game.sim_tick+150
        self.notices=[n for n in self.notices if n['until']>self.game.sim_tick]
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
            if self.game.state=='lost': self.open_score('result')
        return events

    def button(self,y,text,action,width=440,height=42):
        w,h=self.surface.get_size(); c=self.canvas; p=PALETTE
        rect=pg.Rect(w/2-width/2,y-height/2,width,height)
        c.create_rectangle(*rect.topleft,*rect.bottomright,fill=p['cloud'] if rect.collidepoint(pg.mouse.get_pos()) else p['fog'],outline=p['gold'])
        c.create_text(w/2,y,text=text,fill=p['text'],font=('Segoe UI',13,'bold'))
        self.buttons.append((rect,action))

    def draw(self):
        w,h=self.surface.get_size(); self.buttons=[]; c=self.canvas; p=PALETTE
        c.text_scale=1.25 if self.settings.large_text else 1.
        labels=self.settings.key_label
        hint='%s%s%s%s · %s nhảy · %s lướt · %s nạp · %s tỏa · %s dừng'%(labels('move_up'),labels('move_left'),labels('move_down'),labels('move_right'),labels('jump'),labels('dash'),labels('interact'),labels('pulse'),labels('pause'))
        self.scene.draw(self.game,self.yaw,w,h,self.message,total_score=self.campaign.total,colorblind=self.settings.colorblind,
                        reduce_motion=self.settings.reduced_motion,notices=self.notices,controls_hint=hint,interaction_key=labels('interact'))
        if self.screen=='playing': return
        overlay=pg.Surface((w,h),pg.SRCALPHA); overlay.fill((14,20,48,190)); self.surface.blit(overlay,(0,0))
        halfw=min(w/2-20,450); halfh=min(h/2-20,310)
        c.create_rectangle(w/2-halfw,h/2-halfh,w/2+halfw,h/2+halfh,fill=p['sky'],outline=p['gold'],width=2)
        title={'menu':'ĐẢO ĐÈN LỒNG','intro':'ĐÊM %d · %s'%(self.game.night,World.names[self.game.night]),'pause':'ĐÊM ĐANG NGHỈ',
               'settings':'CÀI ĐẶT','bindings':'ĐỔI PHÍM','score-entry':'GHI DANH','leaderboard':'BẢNG XẾP HẠNG',
               'result':'ĐẢO ĐÃ SÁNG LẠI' if self.game.state=='won' else 'THỬ LẠI, MÂY NHÉ','dawn':'BÌNH MINH'}.get(self.screen,'')
        c.create_text(w/2,h/2-260,text=title,fill=p['gold'],font=('Segoe UI',24,'bold'))
        if self.screen=='menu':
            c.create_text(w/2,h/2-150,text='Đèn có thể cạn dầu — giữ đảo sáng tới bình minh.\nMây và ngọn đèn nhỏ đang chờ bạn.',fill=p['text'],font=('Segoe UI',13),width=800)
            for dy,text,action in [(-35,'Bắt đầu · ENTER','new'),(25,'Bảng xếp hạng','leaderboard'),(85,'Cài đặt','settings'),(145,'Thoát','quit')]: self.button(h/2+dy,text,action)
        elif self.screen=='intro':
            story={1:'Ông Đăng: “Đừng sợ đêm. Mỗi đốm sáng là một đường về.”',2:'Ông Đăng: “Qua cầu tre, nhớ nghe tiếng gió lạc.”',3:'Ông Đăng: “Lên tháp chuông, ta sẽ thấy bình minh.”'}[self.game.night]
            hint={1:'Giữ chuột phải hoặc Q,C để xoay camera.',2:'Cầu tre và bục vàng nối hai đảo.',3:'Theo dốc lên tầng một; bục vàng đưa lên tầng chuông.'}[self.game.night]
            c.create_text(w/2,h/2-90,text=story+'\n\nGiữ ít nhất %d/%d đèn sáng tới bình minh (%ds).\nĐèn yếu mất bảo vệ; dùng Tương tác để châm dầu.\n\n'%(self.game.required_lights,len(self.game.lanterns),self.game.duration)+hint,fill=p['text'],font=('Segoe UI',13),width=790)
            self.button(h/2+100,'Vào Đêm · ENTER','play'); self.button(h/2+165,'Về menu','menu')
        elif self.screen=='pause':
            for i,(text,action) in enumerate([('Tiếp tục','resume'),('Chơi lại Đêm','retry'),('Cài đặt','settings'),('Về menu','menu')]): self.button(h/2-115+i*65,text,action)
        elif self.screen=='settings': self.draw_settings(w,h)
        elif self.screen=='bindings':
            c.create_text(w/2,h/2-215,text=self.binding_message or 'Chọn hành động rồi nhấn phím mới. Phím trùng sẽ được báo.',fill=p['gold'],font=('Segoe UI',11),width=820)
            for i,action in enumerate(ACTION_LABELS):
                label=ACTION_LABELS[action]+' : '+', '.join(self.settings.bindings[action]).upper()
                if self.pending_binding==action: label+='  ← PHÍM MỚI?'
                self.button(h/2-170+i*39,label,'bind:'+action,width=660,height=33)
            self.button(h/2+210,'Khôi phục mặc định','bindings-default',height=38)
            self.button(h/2+260,'Quay lại','bindings-back',height=38)
        elif self.screen=='score-entry':
            c.create_text(w/2,h/2-160,text='Tổng các Đêm đã thắng: %d · Số Đêm thắng: %d\nTên3–12chữ/số/_, không khoảng trắng (hỗ trợ tiếng Việt)'%(self.campaign.total,len(self.campaign.scores)),fill=p['text'],font=('Segoe UI',14),width=800)
            c.create_rectangle(w/2-240,h/2-70,w/2+240,h/2-10,fill=p['fog'],outline=p['gold'])
            c.create_text(w/2,h/2-40,text=self.name_text+'▏',fill=p['text'],font=('Segoe UI',22))
            if self.name_error: c.create_text(w/2,h/2+30,text=self.name_error,fill=p['danger'],font=('Segoe UI',12),width=800)
            self.button(h/2+115,'Lưu điểm · ENTER','submit-score'); self.button(h/2+180,'Bỏ qua · ESC','skip-score')
        elif self.screen=='leaderboard':
            c.create_text(w/2,h/2-210,text='TOP10 · Điểm giảm dần · Bằng điểm: đạt trước đứng trước',fill=p['text'],font=('Segoe UI',12))
            for i,entry in enumerate(self.board_entries):
                y=h/2-160+i*31
                when=timestamp(entry['achieved_at']).astimezone(timezone(timedelta(hours=7))).strftime('%d/%m %H:%M')
                c.create_text(w/2-400,y,anchor='w',text='%2d. %s'%(i+1,entry['name']),fill=p['text'],font=('Segoe UI',12))
                c.create_text(w/2-25,y,text='%d điểm · %dĐêm'%(entry['score'],entry['nights_won']),fill=p['gold'],font=('Segoe UI',12))
                c.create_text(w/2+295,y,text=when+' ICT',fill=p['text'],font=('Segoe UI',11))
            if not self.board_entries: c.create_text(w/2,h/2-40,text=self.board.warning or 'Chưa có điểm được lưu.',fill=p['text'],font=('Segoe UI',14),width=800)
            self.button(h/2+230,'Về menu · ENTER','menu')
        elif self.screen=='result':
            c.create_text(w/2,h/2-110,text='Điểm Đêm: %d\nTổng các Đêm đã thắng: %d'%(self.game.score,self.campaign.total),fill=p['text'],font=('Segoe UI',16))
            self.button(h/2+20,'Đêm tiếp theo · ENTER' if self.game.state=='won' and self.game.night<3 else ('Đón Bình Minh · ENTER' if self.game.state=='won' else 'Chơi lại Đêm · ENTER'),'next' if self.game.state=='won' else 'retry')
            self.button(h/2+90,'Về menu','menu')
        elif self.screen=='dawn':
            c.create_text(w/2,h/2-90,text='Ba hòn đảo đã tìm lại ánh sáng.\n\nTổng điểm: %d\nCảm ơn bạn đã giữ đèn cùng Mây.'%self.campaign.total,fill=p['core'],font=('Segoe UI',17),width=800)
            self.button(h/2+110,'Lưu điểm · ENTER','score'); self.button(h/2+175,'Về menu','menu')

    def draw_settings(self,w,h):
        c=self.canvas; p=PALETTE
        for y,label,value in [(h/2-130,'Âm lượng',self.settings.volume),(h/2-60,'Độ nhạy chuột',(self.settings.sensitivity-.05)/.95)]:
            c.create_text(w/2,y-27,text=label+' · %.2f'%(self.settings.volume if label=='Âm lượng' else self.settings.sensitivity),fill=p['text'],font=('Segoe UI',13))
            c.create_rectangle(w/2-180,y-4,w/2+180,y+4,fill=p['fog'],outline=p['gold'])
            xx=w/2-180+360*value; c.create_oval(xx-9,y-9,xx+9,y+9,fill=p['gold'],outline='')
        for offset,key,label in [(5,'colorblind','Bảng màu dễ phân biệt'),(55,'reduced_motion','Giảm chuyển động'),(105,'large_text','Chữ lớn ×1.25')]:
            self.button(h/2+offset,label+': '+('BẬT' if getattr(self.settings,key) else 'TẮT'),key)
        self.button(h/2+155,'Đổi phím','bindings'); self.button(h/2+215,'Quay lại · ESC','back')

    def run(self):
        clock=pg.time.Clock()
        while self.running:
            elapsed=min(clock.tick(60)/1000,.25); self.accumulator+=elapsed
            for event in pg.event.get(): self.handle_event(event)
            while self.accumulator>=DT: self.step_once(); self.accumulator-=DT
            self.draw(); pg.display.flip()
        pg.quit()


def play(seed=12): App(seed).run()
