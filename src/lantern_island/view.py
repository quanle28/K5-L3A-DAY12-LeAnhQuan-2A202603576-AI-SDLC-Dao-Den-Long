"""Small perspective 3D renderer. All decoration is presentation-only."""
import math
import time
import tkinter as tk
from .model import DEFAULT_INPUT, DT, Game, ISLAND_RADIUS, TUNING, distance


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
            self.polygon([q,p,(x,y-radius*1.4,z)], mix(color,"#27203b",.3))

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

    def draw(self, game, yaw, w, h, message="", paused=False, started=True):
        self.w, self.h, self.f = w, h, min(w,h)*.98
        self.sy,self.cy=math.sin(math.radians(yaw)),math.cos(math.radians(yaw))
        self.sp,self.cp=math.sin(.48),math.cos(.48)
        self.eye=[game.pos[0]-self.sy*13, game.pos[1]+8, game.pos[2]-self.cy*13]
        c=self.canvas
        c.delete("all")
        lit=sum(l["lit"] for l in game.lanterns)
        for i in range(20):
            c.create_rectangle(0,h*i/20,w,h*(i+1)/20+1,fill=mix("#080d24","#303454",i/20),outline="")
        # Fixed stars and cloud banks never affect simulation RNG.
        for i in range(48):
            x=(i*173+23)%max(1,int(w)); y=(i*47+31)%max(1,int(h*.38))
            c.create_oval(x,y,x+2,y+2,fill="#a4b9cd",outline="")
        c.create_oval(w*.77,h*.08,w*.77+54,h*.08+54,fill="#ece5c1",outline="")
        for i in range(7):
            x=(i*w/6)-80
            c.create_oval(x,h*.48+(i%2)*22,x+240,h*.73,fill="#353a56",outline="")
        self.faces=[]
        for i in range(48):
            a,b=i*math.tau/48,(i+1)*math.tau/48
            p=(ISLAND_RADIUS*math.sin(a),0,ISLAND_RADIUS*math.cos(a))
            q=(ISLAND_RADIUS*math.sin(b),0,ISLAND_RADIUS*math.cos(b))
            self.polygon([(0,0,0),p,q],mix("#243e43","#607a58",lit/10 + (i%3)*.025))
            self.polygon([p,(p[0]*.86,-5,p[2]*.86),(q[0]*.86,-5,q[2]*.86),q],"#252d3c" if i%2 else "#30394a")
        for _,pts,color in sorted(self.faces,key=lambda f:f[0],reverse=True):
            c.create_polygon(*[v for p in pts for v in p],fill=color,outline=color)
        self.faces=[]
        self.disc((0,.02,0),2.2,"#3d5755")
        for lamp in game.lanterns:
            x,y,z=lamp["pos"]
            if lamp["lit"]:
                self.disc((x,.035,z),TUNING["safe_radius"],"#7e8052")
        # Separate ground pass prevents large clipped triangles hiding actors.
        for _,pts,color in sorted(self.faces,key=lambda f:f[0],reverse=True):
            c.create_polygon(*[v for p in pts for v in p],fill=color,outline=color)
        self.faces=[]
        for lamp in game.lanterns:
            x,y,z=lamp["pos"]
            self.box((x,y,z),.6,3.1,.6,"#9b7562")
            self.box((x,y+2.8,z),2.2,.18,.3,"#c5a078")
            self.jewel((x,y+3.1,z),.85,"#ffd475" if lamp["lit"] else "#6b6570")
            self.cone((x,y+4.2,z),1.15,.5,"#bf7550")
        for i in range(13):
            a=i*math.tau/13+.27
            x,z=27*math.sin(a),27*math.cos(a)
            self.box((x,0,z),.4,1.6,.4,"#61555c")
            self.cone((x,1,z),1.6,4+(i%3)*.4,"#29494b",6)
        for mote in game.motes:
            x,y,z=mote["pos"]
            self.spark((x,y+.7+.16*math.sin(game.tick*.05+x),z),.15,"#ffdc79")
        for shade in game.shades:
            x,y,z=shade["pos"]
            y=.9+.12*math.sin(game.tick*.06+x)
            self.jewel((x,y,z),.7,"#8c80ad" if shade["state"]=="stunned" else "#3e275d")
            self.cone((x,y-1,z),.65,.9,"#50316d")
            self.jewel((x-.22,y+.15,z-.52),.075,"#d6a8ec")
            self.jewel((x+.22,y+.15,z-.52),.075,"#d6a8ec")
        x,y,z=game.pos
        blink=game.tick<game.invuln_until and game.tick%12<6
        self.box((x,y+.22,z),.62,.9,.5,"#e1d5b3" if blink else "#72b9b0")
        self.box((x-.2,y,z),.19,.35,.28,"#253b50")
        self.box((x+.2,y,z),.19,.35,.28,"#253b50")
        self.jewel((x,y+1.4,z),.3,"#edc9a0")
        self.cone((x,y+1.6,z),.88,.45,"#dfb978",12)
        self.box((x+.7,y+.8,z),.08,.8,.08,"#c4a16c")
        self.jewel((x+.7,y+.7,z),.23,"#ffcf75")
        for _,pts,color in sorted(self.faces,key=lambda f:f[0],reverse=True):
            c.create_polygon(*[v for p in pts for v in p],fill=color,outline=color)
        # One fading pulse ring, driven by a real gameplay event.
        age=game.tick-(game.pulse_ready-round(TUNING["pulse_cooldown_s"]*60))
        if game.pulse_ready and 0<=age<30:
            points=[]
            for i in range(65):
                a=i*math.tau/64; r=TUNING["pulse_radius"]*age/30
                p=self.project((x+r*math.sin(a),y+.15,z+r*math.cos(a)))
                if p: points.extend(p)
            if len(points)>3: c.create_line(*points,fill="#ffe2a0",width=3)
        for lamp in game.lanterns:
            p=self.project([lamp["pos"][0],lamp["pos"][1]+5,lamp["pos"][2]])
            if p:
                c.create_text(*p,text=lamp["id"]+("  ✓" if lamp["lit"] else "  %d/10"%lamp["deposited"]),fill="#ffe6b1",font=("Segoe UI",10,"bold"))
        c.create_rectangle(20,18,355,135,fill="#111c2f",outline="#3c5365")
        c.create_text(38,39,anchor="w",text="ĐẢO ĐÈN LỒNG",fill="#ffdc94",font=("Segoe UI",17,"bold"))
        c.create_text(38,68,anchor="w",text="Đêm 1 · Đảo Bến   |   Đèn %d / 5"%lit,fill="#e6e4d8",font=("Segoe UI",11))
        c.create_text(38,94,anchor="w",text="Lửa %s    Đom đóm %d / 12"%("♥ "*game.flames,game.carried),fill="#ffbe82",font=("Segoe UI",11))
        seconds=max(0,math.ceil(game.time_left))
        c.create_text(38,119,anchor="w",text="%02d:%02d    Điểm %d"%(seconds//60,seconds%60,game.score),fill="#c3d5d7",font=("Segoe UI",11))
        # Small world-oriented map lets the player navigate behind the camera.
        mx,my=w-100,100
        c.create_oval(mx-72,my-72,mx+72,my+72,fill="#122b35",outline="#64807a")
        for lamp in game.lanterns:
            px,py=mx+lamp["pos"][0]*2,my-lamp["pos"][2]*2
            c.create_oval(px-5,py-5,px+5,py+5,fill="#ffd478" if lamp["lit"] else "#74667b",outline="")
        for shade in game.shades:
            px,py=mx+shade["pos"][0]*2,my-shade["pos"][2]*2
            c.create_oval(px-2,py-2,px+2,py+2,fill="#b291d3",outline="")
        px,py=mx+x*2,my-z*2
        c.create_oval(px-4,py-4,px+4,py+4,fill="#8ee3da",outline="")
        c.create_text(mx,my+86,text="ĐẢO BẾN",fill="#9bbab7",font=("Segoe UI",9))
        c.create_rectangle(0,h-62,w,h,fill="#101b2b",outline="")
        c.create_text(w/2,h-42,text="WASD / ↑↓←→  Di chuyển     SPACE  Nhảy     E  Nạp đèn     F  Tỏa sáng (3)     Q / C  Xoay camera",fill="#d3ddd9",font=("Segoe UI",10))
        c.create_text(w/2,h-19,text=message or "Thắp 5 đèn trước bình minh · Đèn sáng che chở Mây · P tạm dừng · R chơi lại · Esc thoát",fill="#d7b987",font=("Segoe UI",10))
        if not started or paused or game.state!="playing":
            c.create_rectangle(w/2-285,h/2-130,w/2+285,h/2+130,fill="#111e32",outline="#ad946e",width=2)
            title="MỘT ĐỐM SÁNG, MỘT HY VỌNG"
            body="Mây mang đèn nhỏ đi qua biển sương.\nGom đom đóm vàng, đến gần cột đèn rồi nhấn E.\nNhấn F để xua Bóng Mực; giữ lại đủ sáng cho 5 đèn."
            footer="ENTER · Bắt đầu đêm 1"
            if paused:
                title,body,footer="ĐÊM ĐANG NGHỈ","Ánh sáng sẽ chờ bạn trở lại.","P · Tiếp tục"
            if game.state!="playing":
                title="ĐẢO ĐÃ SÁNG LẠI" if game.state=="won" else "HẸN MÂY MỘT ĐÊM KHÁC"
                body="Điểm: %d\n%s"%(game.score,"Năm ngọn đèn đã nối lại biển mây." if game.state=="won" else "Hãy tận dụng vùng sáng và tỏa sáng để giữ lửa.")
                footer="R / ENTER · Chơi lại    |    ESC · Thoát"
            c.create_text(w/2,h/2-78,text=title,fill="#ffdb93",font=("Segoe UI",18,"bold"))
            c.create_text(w/2,h/2,text=body,fill="#c7d7da",font=("Segoe UI",12),justify="center")
            c.create_text(w/2,h/2+86,text=footer,fill="#87d4c9",font=("Segoe UI",12,"bold"))


class App:
    def __init__(self, root, seed=12, schedule=True):
        self.root,self.seed=root,seed
        root.title("Đảo Đèn Lồng · Đêm 1 – Đảo Bến")
        root.geometry("1152x760")
        root.minsize(900,600)
        self.canvas=tk.Canvas(root,highlightthickness=0,bg="#080d24")
        self.canvas.pack(fill="both",expand=True)
        self.scene=Scene(self.canvas)
        self.keys=set()
        self.pending_release={}
        self.started=False
        self.paused=False
        self.yaw=0
        self.game=Game(seed)
        self.message=""
        self.message_until=0
        self.accumulator=0
        self.last=time.perf_counter()
        root.bind("<KeyPress>",self.key_down)
        root.bind("<KeyRelease>",self.key_up)
        root.bind("<FocusOut>",self.focus_out)
        self.scheduled=schedule
        if schedule: self.frame()

    def restart(self):
        self.game=Game(self.seed)
        self.started=True
        self.paused=False
        self.yaw=0
        self.keys.clear()
        self.pending_release.clear()
        self.accumulator=0
        self.message=""

    def key_down(self,event):
        key=event.keysym.lower()
        # A delayed release filters the release/press pairs emitted by X11 repeat.
        if key in self.pending_release:
            self.root.after_cancel(self.pending_release.pop(key))
        if key in self.keys: return
        self.keys.add(key)
        if key=="escape": self.root.destroy(); return
        if key=="r" or key=="return" and self.game.state!="playing": self.restart()
        elif key=="return": self.started=True
        elif key=="p" and self.started: self.paused=not self.paused

    def key_up(self,event):
        key=event.keysym.lower()
        def release():
            self.keys.discard(key)
            self.pending_release.pop(key,None)
        self.pending_release[key]=self.root.after_idle(release)

    def focus_out(self,event):
        self.keys.clear()
        for callback in self.pending_release.values(): self.root.after_cancel(callback)
        self.pending_release.clear()
        if self.started and self.game.state=="playing": self.paused=True

    def update(self):
        if self.paused or not self.started: return
        k=self.keys
        self.yaw+=(int("c" in k)-int("q" in k))*1.5
        controls=dict(DEFAULT_INPUT)
        controls.update(move=[int("d" in k or "right" in k)-int("a" in k or "left" in k),
                              int("w" in k or "up" in k)-int("s" in k or "down" in k)],
                        cam_yaw_deg=self.yaw,jump="space" in k,interact="e" in k,pulse="f" in k)
        events=self.game.step(controls)
        for e in events:
            if e["name"]=="lantern_lit": self.message="Một ngọn đèn đã thức giấc! Vùng sáng bảo vệ Mây."
            elif e["name"]=="player_hit": self.message="Mây mất một ngọn lửa! Tìm vùng sáng hoặc nhấn F."
            elif e["name"]=="pulse": self.message="Ánh sáng đã xua %d Bóng Mực."%len(e["data"]["stunned_ids"])
            else: continue
            self.message_until=self.game.tick+180
        if self.game.tick>self.message_until: self.message=""
        near=[l for l in self.game.lanterns if not l["lit"] and distance(l["pos"],self.game.pos)<=TUNING["interact_radius"]]
        if near: self.message="E · Nạp ánh sáng cho %s (%d / 10)"%(near[0]["id"],near[0]["deposited"])

    def frame(self):
        now=time.perf_counter()
        self.accumulator+=min(now-self.last,.2)
        self.last=now
        while self.accumulator>=DT:
            self.update()
            self.accumulator-=DT
        self.scene.draw(self.game,self.yaw,max(900,self.canvas.winfo_width()),max(600,self.canvas.winfo_height()),self.message,self.paused,self.started)
        if self.scheduled: self.root.after(25,self.frame)


def play(seed=12):
    root=tk.Tk()
    App(root,seed)
    root.mainloop()
