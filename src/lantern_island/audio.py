"""Original synthesized music and effects. No downloaded audio assets."""
from array import array
import math

SFX=dict(mote_picked=(880,1100),lantern_lit=(523,659,784),pulse=(330,660,990),
         player_hit=(220,140),jump=(440,600),dash=(660,880),won=(523,659,784,1046),
         lost=(392,330,261),shade_spawned=(130,110),countdown=(1200,),wind=(300,400,300),
         charm_picked=(784,988,1174),drifter_steal=(220,330))


def pcm(notes,seconds=.1,rate=22050):
    samples=array('h')
    for freq in notes:
        n=int(seconds*rate)
        for i in range(n):
            t=i/rate
            envelope=min(1,i/(rate*.01))*max(0,1-i/n)
            value=math.sin(math.tau*freq*t)+.2*math.sin(math.tau*freq*2*t)
            samples.append(round(value*5000*envelope))
    return samples.tobytes()


class Audio:
    def __init__(self,pg,volume=.5):
        self.pg=pg; self.available=False; self.sounds={}; self.music={}; self.history=[]
        try:
            pg.mixer.quit(); pg.mixer.init(frequency=22050,size=-16,channels=1,buffer=512)
            pg.mixer.set_num_channels(16); pg.mixer.set_reserved(1)
            self.sounds={name:pg.mixer.Sound(buffer=pcm(notes)) for name,notes in SFX.items()}
            for night in (1,2,3):
                notes=tuple(f*(1+(night-1)*.05) for f in (220,261.63,329.63,293.66,220,196,261.63,246.94))
                self.music[night]=pg.mixer.Sound(buffer=pcm(notes,.55))
            self.available=True; self.volume(volume)
        except pg.error: pass
    def volume(self,value):
        self.level=value
        for s in self.sounds.values(): s.set_volume(value*.65)
        for s in self.music.values(): s.set_volume(value*.25)
    def start(self,night):
        if self.available: self.pg.mixer.Channel(0).play(self.music[night],loops=-1)
    def play(self,name):
        self.history.append(name)
        if self.available and name in self.sounds: self.sounds[name].play()
    def pause(self,paused):
        if self.available:
            self.pg.mixer.pause() if paused else self.pg.mixer.unpause()
