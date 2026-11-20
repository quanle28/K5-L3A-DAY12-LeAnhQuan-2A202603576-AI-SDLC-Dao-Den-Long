"""Ticket-02 map coordinates and walkable surface/collision queries."""
import math


def ring(radius, count, center=(0,0,0), start=0):
    return [[center[0]+radius*math.cos(math.radians(start+i*360/count)),
             center[1],center[2]+radius*math.sin(math.radians(start+i*360/count))] for i in range(count)]


class World:
    names={1:'Đảo Bến',2:'Đảo Cau',3:'Đảo Chuông'}

    def __init__(self,night):
        self.night=night
        self.spawn=[0.,0.,0.] if night!=3 else [0.,0.,-30.]
        self.pads=[]
        if night==1:
            self.islands=[(0,0,40)]
            self.lamps=[[0,0,25],[23.8,0,7.7],[14.7,0,-20.2],[-14.7,0,-20.2],[-23.8,0,7.7]]
            self.mote_points=ring(12,8)+ring(33,16)
            self.fog_points=ring(37,12,start=15)
        elif night==2:
            self.islands=[(0,0,28),(70,0,28)]
            self.lamps=[[0,0,20],[17,0,-10],[-17,0,-10],[70,0,20],[87,0,-10],[53,0,-10]]
            self.mote_points=sum((ring(10,4,(x,0,0))+ring(22,8,(x,0,0)) for x in (0,70)),[])
            self.fog_points=sum((ring(26,8,(x,0,0),22.5) for x in (0,70)),[])
            self.pads=[([20,0,18],[70,0,0],14,24),([50,0,-18],[0,0,0],14,24)]
        else:
            self.islands=[(0,0,45)]
            self.lamps=[[0,6,6],[18,3,10],[-18,3,10],[35,0,-10],[-35,0,-10],[20,0,-35],[-20,0,-35]]
            self.mote_points=ring(34,18)+[[18*math.cos(math.radians(a)),3,18*math.sin(math.radians(a))] for a in range(20,161,20)]+ring(5,4,(0,6,0),45)
            self.fog_points=ring(43,16)
            self.pads=[([0,3,13],[0,3,0],12,8)]

    def floor(self,x,z):
        if self.night==2:
            if 26<=x<=44 and -2<=z<=2: return 0.
        if not any(math.hypot(x-cx,z-cz)<=r+1e-9 for cx,cz,r in self.islands): return None
        if self.night!=3: return 0.
        r=math.hypot(x,z)
        if r<=8: return 6.
        if 12<=r<=24 and z>0: return 3.
        for angle in (30,150):
            a=math.radians(angle)
            along=x*math.cos(a)+z*math.sin(a)
            across=-x*math.sin(a)+z*math.cos(a)
            if 24<=along<=30 and abs(across)<=1.5:
                return (30-along)/2
        return 0.

    def blocked(self,old,new):
        if self.night==3 and math.hypot(new[0],new[2])<2 and 5.99<=new[1]<14:
            return True
        floor=self.floor(new[0],new[2])
        # Ramps can rise only a small amount per physics step, vertical walls cannot.
        slope_step=max(.11,math.hypot(new[0]-old[0],new[2]-old[2])*.51+.001)
        return floor is not None and floor>max(old[1],new[1])+slope_step

    def pad(self,pos):
        for p,target,vy,speed in self.pads:
            if math.hypot(pos[0]-p[0],pos[2]-p[2])<=1 and abs(pos[1]-p[1])<=.1:
                dx,dz=target[0]-p[0],target[2]-p[2]
                d=math.hypot(dx,dz)
                return [dx/d*speed,vy,dz/d*speed]
        return None


PALETTE=dict(sky='#0E1430',fog='#1B2350',grass='#2F5D50',sand='#C9B48A',wood='#6B4A2F',cloud='#12384A',
             lamp='#FFB347',core='#FFE9B0',unlit='#5B5F6E',mote='#FFF6C2',halo='#FFE58A',
             shade='#120A1A',outline='#7A3CFF',stunned='#3A3450',coat='#E8E2D0',red='#C8102E',
             gold='#F2C14E',drifter='#8FA3B8',danger='#FF5A5F',text='#F5F1E6')
