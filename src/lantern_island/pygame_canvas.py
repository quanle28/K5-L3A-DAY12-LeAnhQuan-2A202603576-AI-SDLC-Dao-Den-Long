"""Raster drawing backend implementing the scene's small Canvas interface."""
import os
from pathlib import Path
import sys
from collections import OrderedDict
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.runtime'))
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import pygame as pg


class PygameCanvas:
    def __init__(self,surface):
        self.surface=surface; self.fonts={}; self.text_cache={}; self.sprite_bases={}; self.sprite_cache=OrderedDict()
        self.text_scale=1.; self.rendered_font_sizes=[]
    def delete(self,*args): self.surface.fill('#0E1430'); self.rendered_font_sizes=[]
    def create_rectangle(self,x1,y1,x2,y2,**kw):
        rect=pg.Rect(round(x1),round(y1),max(0,round(x2-x1)),max(0,round(y2-y1)))
        if kw.get('fill'): pg.draw.rect(self.surface,kw['fill'],rect)
        if kw.get('outline'): pg.draw.rect(self.surface,kw['outline'],rect,int(kw.get('width',1)))
    def create_oval(self,x1,y1,x2,y2,**kw):
        rect=pg.Rect(round(x1),round(y1),max(0,round(x2-x1)),max(0,round(y2-y1)))
        if kw.get('fill'): pg.draw.ellipse(self.surface,kw['fill'],rect)
        if kw.get('outline'): pg.draw.ellipse(self.surface,kw['outline'],rect,int(kw.get('width',1)))
    def create_polygon(self,*coords,**kw):
        points=list(zip(coords[::2],coords[1::2]))
        if len(points)<3: return
        w,h=self.surface.get_size()
        xs,ys=zip(*points)
        if max(xs)<0 or min(xs)>w or max(ys)<0 or min(ys)>h: return
        # Near-plane projection can produce enormous offscreen coordinates.
        # Clip to the viewport before SDL rasterization; pixels and simulation stay unchanged.
        if min(xs)<0 or max(xs)>w or min(ys)<0 or max(ys)>h:
            for axis,bound,positive in ((0,0,True),(0,w,False),(1,0,True),(1,h,False)):
                clipped=[]
                for a,b in zip(points,points[1:]+points[:1]):
                    ina=a[axis]>=bound if positive else a[axis]<=bound
                    inb=b[axis]>=bound if positive else b[axis]<=bound
                    if ina: clipped.append(a)
                    if ina!=inb:
                        t=(bound-a[axis])/(b[axis]-a[axis])
                        clipped.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
                points=clipped
                if len(points)<3: return
        pg.draw.polygon(self.surface,kw.get('fill','#fff'),points)
    def create_line(self,*coords,**kw):
        points=list(zip(coords[::2],coords[1::2]))
        if len(points)>1: pg.draw.lines(self.surface,kw.get('fill','#fff'),False,points,int(kw.get('width',1)))
    def create_text(self,x,y,**kw):
        spec=kw.get('font',('Segoe UI',11)); size=round(max(18,round(spec[1]*1.2))*self.text_scale)
        self.rendered_font_sizes.append(size)
        key=(size,'bold' in spec)
        if key not in self.fonts:
            path=pg.font.match_font('segoeui,dejavusans,arial',bold=key[1])
            self.fonts[key]=pg.font.Font(path,size)
        font=self.fonts[key]; lines=str(kw.get('text','')).split('\n')
        if kw.get('width'):
            wrapped=[]
            for line in lines:
                current=''
                for word in line.split(' '):
                    candidate=(current+' '+word).strip()
                    if current and font.size(candidate)[0]>kw['width']: wrapped.append(current); current=word
                    else: current=candidate
                wrapped.append(current)
            lines=wrapped
        for i,line in enumerate(lines):
            cache=(key,line,kw.get('fill','#ffffff'))
            if cache not in self.text_cache:
                if len(self.text_cache)>512: self.text_cache.clear()
                # Some system fonts lack U+26A0. Draw that warning as geometry below.
                self.text_cache[cache]=font.render(line.replace('⚠','  '),True,cache[2])
            image=self.text_cache[cache]
            rect=image.get_rect()
            if kw.get('anchor')=='w': rect.midleft=(x,y+(i-(len(lines)-1)/2)*font.get_linesize())
            else: rect.center=(x,y+(i-(len(lines)-1)/2)*font.get_linesize())
            self.surface.blit(image,rect)
            if '⚠' in line:
                height=max(10,round(size*.7)); cx=rect.left+height/2; cy=rect.centery
                color=kw.get('fill','#ffffff'); stroke=max(1,round(size/16))
                pg.draw.polygon(self.surface,color,[(cx,cy-height/2),(cx-height/2,cy+height/2),(cx+height/2,cy+height/2)],stroke)
                pg.draw.line(self.surface,color,(cx,cy-height*.15),(cx,cy+height*.12),stroke)
                pg.draw.circle(self.surface,color,(round(cx),round(cy+height*.32)),max(1,stroke//2))

    def create_sprite(self,kind,x,y,width,height,body,outline):
        """Cached, high-resolution impostor for the same standard shade in every mode."""
        key=(kind,body,outline)
        if key not in self.sprite_bases:
            image=pg.Surface((128,176),pg.SRCALPHA)
            pg.draw.polygon(image,body,[(64,4),(117,86),(64,170),(11,86)])
            pg.draw.polygon(image,outline,[(8,88),(25,99),(103,99),(120,88),(111,105),(17,105)])
            for ex in (45,82): pg.draw.polygon(image,outline,[(ex,68),(ex+5,76),(ex,84),(ex-5,76)])
            self.sprite_bases[key]=image
        size=(max(2,int(width)),max(3,int(height))); cache=key+size
        if cache not in self.sprite_cache:
            self.sprite_cache[cache]=pg.transform.smoothscale(self.sprite_bases[key],size)
            if len(self.sprite_cache)>256: self.sprite_cache.popitem(last=False)
        else: self.sprite_cache.move_to_end(cache)
        image=self.sprite_cache[cache]
        self.surface.blit(image,(round(x-size[0]/2),round(y-size[1]/2)))
