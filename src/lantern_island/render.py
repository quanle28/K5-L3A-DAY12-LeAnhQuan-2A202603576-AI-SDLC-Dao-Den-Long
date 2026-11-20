"""Small perspective 3D renderer. All decoration is presentation-only."""
import math
import time
from functools import lru_cache
from .model import TUNING, distance
from .maps import PALETTE


@lru_cache(maxsize=256)
def mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join("%02x" % int(int(a[i:i+2], 16) * (1-t) + int(b[i:i+2], 16) * t) for i in (0, 2, 4))


class Scene:
    def __init__(self, canvas):
        self.canvas = canvas

    def camera_point(self, p):
        x, y, z = (p[i] - self.eye[i] for i in range(3))
        return (x*self.cy - z*self.sy,
                x*self.sy*self.sp + y*self.cp + z*self.cy*self.sp,
                x*self.sy*self.cp - y*self.sp + z*self.cy*self.cp)

    def project(self, p):
        x, y, z = self.camera_point(p)
        if z <= .2:
            return None
        return self.w/2 + x*self.f/z, self.h*.53-y*self.f/z

    def polygon(self, points, color):
        # Clip in camera space, so ground triangles remain stable near the camera.
        pts = [self.camera_point(p) for p in points]
        clipped = []
        for a, b in zip(pts, pts[1:] + pts[:1]):
            ina, inb = a[2] >= .2, b[2] >= .2
            if ina:
                clipped.append(a)
            if ina != inb:
                t = (.2-a[2]) / (b[2]-a[2])
                clipped.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(3)))
        if len(clipped) < 3:
            return
        coords = [(self.w/2+x*self.f/z, self.h*.53-y*self.f/z) for x, y, z in clipped]
        self.faces.append((sum(p[2] for p in pts)/len(pts), coords, color))

    def box(self, pos, sx, sy, sz, color):
        x, y, z = pos
        v = [(x+dx*sx/2, y+dy*sy, z+dz*sz/2) for dy in (0, 1) for dz in (-1, 1) for dx in (-1, 1)]
        for indexes, shade in [([0,1,3,2],.35), ([4,5,7,6],0), ([0,1,5,4],.22),
                               ([2,3,7,6],.1), ([0,2,6,4],.28), ([1,3,7,5],.16)]:
            self.polygon([v[i] for i in indexes], mix(color, "#08121e", shade))

    def cone(self, pos, radius, height, color, n=8):
        x, y, z = pos
        for i in range(n):
            a, b = i*math.tau/n, (i+1)*math.tau/n
            self.polygon([(x+radius*math.sin(a), y, z+radius*math.cos(a)),
                          (x, y+height, z), (x+radius*math.sin(b), y, z+radius*math.cos(b))],
                         mix(color, "#0d1826", .12 + .16*(i % 3)))

    def jewel(self, pos, radius, color):
        x, y, z = pos
        for i in range(6):
            a, b = i*math.tau/6, (i+1)*math.tau/6
            p, q = (x+radius*math.sin(a),y,z+radius*math.cos(a)), (x+radius*math.sin(b),y,z+radius*math.cos(b))
            self.polygon([p,q,(x,y+radius*1.4,z)], color)
            self.polygon([q,p,(x,y-radius*1.4,z)], mix(color,"#27203b",.04))

    def spark(self, pos, radius, color):
        p = self.project(pos)
        depth = self.camera_point(pos)[2]
        if p is not None:
            x,y=p
            r=max(1.5,self.f*radius/depth)
            self.faces.append((depth,[(x-r,y),(x,y-r*1.5),(x+r,y),(x,y+r*1.5)],color))

    def disc(self, pos, radius, color, n=32):
        x,y,z = pos
        for i in range(n):
            a,b=i*math.tau/n,(i+1)*math.tau/n
            self.polygon([(x,y,z),(x+radius*math.sin(a),y,z+radius*math.cos(a)),
                          (x+radius*math.sin(b),y,z+radius*math.cos(b))], color)

    def flush_faces(self):
        for _,points,color in sorted(self.faces,key=lambda f:f[0],reverse=True):
            self.canvas.create_polygon(*[v for p in points for v in p],fill=color,outline=color)
        self.faces=[]

    def ring_surface(self,inner,outer,y,half=False,color=None):
        color=color or PALETTE['grass']
        count=32
        for i in range(count):
            a,b=i*math.tau/count,(i+1)*math.tau/count
            if half and math.sin((a+b)/2)<=0: continue
            p=[(inner*math.cos(a),y,inner*math.sin(a)),(outer*math.cos(a),y,outer*math.sin(a)),
               (outer*math.cos(b),y,outer*math.sin(b)),(inner*math.cos(b),y,inner*math.sin(b))]
            self.polygon(p,color)

    def draw(self,game,yaw,w,h,message='',paused=False,started=True,total_score=0):
        self.w,self.h,self.f=w,h,min(w,h)*.98
        self.sy,self.cy=math.sin(math.radians(yaw)),math.cos(math.radians(yaw))
        self.sp,self.cp=math.sin(.48),math.cos(.48)
        self.eye=[game.pos[0]-self.sy*13,game.pos[1]+8,game.pos[2]-self.cy*13]
        c=self.canvas; p=PALETTE
        c.delete('all')
        c.create_rectangle(0,0,w,h,fill=p['sky'],outline='')
        for i in range(35):
            x=(i*173+23)%int(w); y=(i*47+31)%max(1,int(h*.35))
            c.create_oval(x,y,x+2,y+2,fill=p['core'],outline='')
        c.create_oval(w*.78,h*.1,w*.78+48,h*.1+48,fill=p['core'],outline='')
        for i in range(6):
            c.create_oval(i*w/5-100,h*.48,w*i/5+250,h*.8,fill=p['fog'],outline='')
        c.create_rectangle(0,h*.7,w,h,fill=p['cloud'],outline='')
        self.faces=[]
        lit=sum(l['lit'] for l in game.lanterns)
        self.ambient=.15+.55*lit/len(game.lanterns)
        grass=mix(p['grass'],'#000000',.1*(1-self.ambient))
        for cx,cz,r in game.world.islands:
            for i in range(40):
                a,b=i*math.tau/40,(i+1)*math.tau/40
                v=(cx+r*math.cos(a),0,cz+r*math.sin(a)); q=(cx+r*math.cos(b),0,cz+r*math.sin(b))
                self.polygon([(cx,0,cz),v,q],grass)
                self.polygon([v,(cx+(v[0]-cx)*.85,-5,cz+(v[2]-cz)*.85),
                              (cx+(q[0]-cx)*.85,-5,cz+(q[2]-cz)*.85),q],p['sand'])
        if game.night==2:
            self.polygon([(26,.02,-2),(44,.02,-2),(44,.02,2),(26,.02,2)],p['wood'])
            for x in range(26,44):
                self.polygon([(x,.04,-2),(x+.06,.04,-2),(x+.06,.04,2),(x,.04,2)],mix(p['wood'],'#000000',.08))
        self.flush_faces()
        if game.night==3:
            self.ring_surface(12,24,3,True,grass); self.ring_surface(0,8,6,False,grass)
            for radius,height,half in [(12,3,True),(24,3,True),(8,6,False)]:
                for i in range(32):
                    a,b=i*math.tau/32,(i+1)*math.tau/32
                    if half and math.sin((a+b)/2)<=0: continue
                    x,z=radius*math.cos(a),radius*math.sin(a); xx,zz=radius*math.cos(b),radius*math.sin(b)
                    self.polygon([(x,0,z),(xx,0,zz),(xx,height,zz),(x,height,z)],p['sand'])
            for angle in (30,150):
                a=math.radians(angle); u=(math.cos(a),math.sin(a)); v=(-u[1],u[0])
                self.polygon([(r*u[0]+sgn*1.5*v[0],y,r*u[1]+sgn*1.5*v[1]) for r,y,sgn in [(30,0,-1),(30,0,1),(24,3,1),(24,3,-1)]],p['wood'])
            for sign in (-1,1):
                self.polygon([(12*sign,0,0),(24*sign,0,0),(24*sign,3,0),(12*sign,3,0)],p['sand'])
            self.flush_faces()
        for lamp in game.lanterns:
            if lamp['lit']:
                x,y,z=lamp['pos']; self.disc((x,y+.025,z),6,mix(grass,p['lamp'],.25),24)
        for pad,target,vy,speed in game.world.pads:
            self.disc((pad[0],pad[1]+.03,pad[2]),1,p['gold'],16)
        self.flush_faces()
        if game.night==3:
            for i in range(16):
                a,b=i*math.tau/16,(i+1)*math.tau/16
                self.polygon([(2*math.cos(a),6,2*math.sin(a)),(2*math.cos(b),6,2*math.sin(b)),
                              (2*math.cos(b),14,2*math.sin(b)),(2*math.cos(a),14,2*math.sin(a))],p['wood'])
            self.cone((0,14,0),2.6,1.8,p['gold'],12)
        for l in game.lanterns:
            x,y,z=l['pos']; self.box((x,y,z),.45,3,.45,p['wood'])
            self.jewel((x,y+3,z),.7,p['lamp'] if l['lit'] else p['unlit'])
            if l['lit']: self.spark((x,y+3,z),.24,p['core'])
            self.cone((x,y+4,z),1,.4,p['red'])
        for m in game.motes:
            x,y,z=m['pos']; y+=.6+.13*math.sin(game.sim_tick*.06+x)
            self.spark((x,y,z),.22,p['halo']); self.spark((x,y,z),.11,p['mote'])
        for s in game.shades:
            x,y,z=s['pos']; color=p['stunned'] if s['state']=='stunned' else p['shade']
            self.jewel((x,y,z),.75,color); self.cone((x,y-.15,z),.77,.08,p['outline'])
            self.spark((x-.22,y+.1,z-.55),.06,p['mote']); self.spark((x+.22,y+.1,z-.55),.06,p['mote'])
        for d in game.drifters:
            x,y,z=d['pos']; self.jewel((x,y+.4,z),.4,p['drifter'])
            self.box((x,y,z),.25,.1,1.7,p['drifter'])
        for charm in game.charms:
            if charm['available']:
                x,y,z=charm['pos']; self.box((x,y+.5,z),.7,1,.15,p['gold']); self.box((x,y+.55,z-.1),.55,.85,.15,p['red'])
        x,y,z=game.pos
        if not game.respawn_ticks:
            self.box((x,y+.22,z),.65,.9,.5,p['coat']); self.box((x,y+1.0,z),.7,.14,.55,p['red'])
            for dx in (-.2,.2): self.box((x+dx,y,z),.18,.3,.28,p['wood'])
            self.jewel((x,y+1.4,z),.3,p['sand']); self.cone((x,y+1.6,z),.88,.45,p['sand'],10)
            self.box((x+.7,y+.8,z),.06,.7,.06,p['wood']); self.jewel((x+.7,y+.65,z),.22,p['lamp'])
        self.flush_faces()
        if game.last_pulse:
            tick,origin=game.last_pulse; age=game.sim_tick-tick
            if age<30:
                coords=[]; radius=5*min(1,(age+1)/15)
                for i in range(49):
                    a=i*math.tau/48
                    q=self.project([origin[0]+radius*math.cos(a),origin[1]+.8,origin[2]+radius*math.sin(a)])
                    if q: coords.extend(q)
                if len(coords)>3: c.create_line(*coords,fill=p['core'],width=2)
        if self.wind_warning(game):
            for i in range(12):
                xx=(i*113+game.sim_tick*4)%w; yy=130+(i*53)%int(h*.5)
                c.create_polygon(xx,yy,xx+13,yy-5,xx+20,yy+3,xx+5,yy+5,fill=p['gold'])
        for lamp in game.lanterns:
            point=self.project([lamp['pos'][0],lamp['pos'][1]+4.6,lamp['pos'][2]])
            if point: c.create_text(*point,text=lamp['id']+(' ✓' if lamp['lit'] else ' %d/10'%lamp['deposited']),fill=p['text'],font=('Segoe UI',10,'bold'))
        self.hud(game,w,h,message,total_score)

    @staticmethod
    def wind_warning(game):
        return game.night==3 and game.wind_enabled and (game.sim_tick%1800>=1680 or game.wind['active'])

    def hud(self,g,w,h,message,total_score):
        c=self.canvas; p=PALETTE; lit=sum(l['lit'] for l in g.lanterns)
        c.create_rectangle(16,16,250,104,fill=p['fog'],outline=p['gold'])
        c.create_text(30,39,anchor='w',text='NGỌN LỬA  '+'♥ '*g.flames,fill=p['lamp'],font=('Segoe UI',14,'bold'))
        c.create_text(30,73,anchor='w',text='Đêm %d · %s'%(g.night,g.world.names[g.night]),fill=p['text'],font=('Segoe UI',11))
        c.create_rectangle(w/2-90,16,w/2+90,80,fill=p['fog'],outline=p['gold'])
        seconds=max(0,math.ceil(g.time_left)); danger=seconds<=30
        c.create_text(w/2,40,text='%02d:%02d'%(seconds//60,seconds%60),fill=p['danger'] if danger and g.tick%30<15 else p['text'],font=('Segoe UI',25,'bold'))
        c.create_rectangle(w-255,16,w-16,104,fill=p['fog'],outline=p['gold'])
        c.create_text(w-135,40,text='ĐÈN %d / %d'%(lit,len(g.lanterns)),fill=p['text'],font=('Segoe UI',14,'bold'))
        c.create_text(w-135,75,text='Điểm %d · Tổng %d'%(g.score,total_score),fill=p['gold'],font=('Segoe UI',11))
        for i in range(10):
            xx=w/2-150+i*30
            c.create_rectangle(xx,h-64,xx+24,h-41,fill=p['mote'] if i<g.carried else p['fog'],outline=p['gold'])
        c.create_text(w/2,h-23,text='WASD · SPACE nhảy · SHIFT lướt · F tỏa sáng · P / ESC tạm dừng',fill=p['text'],font=('Segoe UI',10))
        c.create_text(w-110,h-63,text='Lướt %.1fs'%max(0,g.dash_cd_ticks/60),fill=p['gold'],font=('Segoe UI',11))
        c.create_text(w-110,h-39,text='Tỏa sáng %.1fs'%max(0,g.pulse_cd_ticks/60),fill=p['lamp'],font=('Segoe UI',11))
        # Actual cooldown icons, not just text: dash chevrons and an eight-ray pulse.
        xx=w-220; yy=h-63
        dash_color=p['unlit'] if g.dash_cd_ticks else p['gold']
        c.create_polygon(xx-10,yy-8,xx,yy,xx-10,yy+8,xx-4,yy+8,xx+7,yy,xx-4,yy-8,fill=dash_color)
        yy=h-39; pulse_color=p['unlit'] if g.pulse_cd_ticks else p['lamp']
        c.create_oval(xx-4,yy-4,xx+4,yy+4,fill=pulse_color,outline='')
        for i in range(8):
            a=i*math.tau/8
            c.create_line(xx+7*math.cos(a),yy+7*math.sin(a),xx+12*math.cos(a),yy+12*math.sin(a),fill=pulse_color,width=2)
        if g.charm_ticks: c.create_text(110,h-58,text='BÙA GIÓ %.1fs'%(g.charm_ticks/60),fill=p['red'],font=('Segoe UI',12,'bold'))
        unlit=[l for l in g.lanterns if not l['lit']]
        if unlit:
            nearest=min(unlit,key=lambda e:(distance(g.pos,e['pos']),e['id']))
            if distance(g.pos,nearest['pos'])<=2:
                c.create_text(w/2,h-105,text='E — Nạp ánh sáng (%d/10)'%nearest['deposited'],fill=p['gold'],font=('Segoe UI',16,'bold'))
            else:
                projected=self.project(nearest['pos'])
                if projected is None or not (20<projected[0]<w-20 and 110<projected[1]<h-110):
                    dx,dz=nearest['pos'][0]-g.pos[0],nearest['pos'][2]-g.pos[2]
                    xx=dx*self.cy-dz*self.sy; forward=dx*self.sy+dz*self.cy
                    a=math.atan2(xx,forward); px=w/2+math.sin(a)*w*.37; py=h/2-math.cos(a)*h*.28
                    c.create_polygon(px+math.sin(a)*16,py-math.cos(a)*16,px+math.cos(a)*9,py+math.sin(a)*9,px-math.cos(a)*9,py-math.sin(a)*9,fill=p['gold'])
                    c.create_text(px,py+28,text=nearest['id']+' · %.0fm'%distance(g.pos,nearest['pos']),fill=p['gold'],font=('Segoe UI',10))
        if message: c.create_text(w/2,105,text=message,fill=p['gold'],font=('Segoe UI',12,'bold'))

