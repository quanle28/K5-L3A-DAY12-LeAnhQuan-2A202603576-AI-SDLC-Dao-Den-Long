"""Raster drawing backend implementing the scene's small Canvas interface."""
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.runtime'))
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import pygame as pg


class PygameCanvas:
    def __init__(self,surface): self.surface=surface; self.fonts={}; self.text_cache={}
    def delete(self,*args): self.surface.fill('#0E1430')
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
        if len(points)>=3: pg.draw.polygon(self.surface,kw.get('fill','#fff'),points)
    def create_line(self,*coords,**kw):
        points=list(zip(coords[::2],coords[1::2]))
        if len(points)>1: pg.draw.lines(self.surface,kw.get('fill','#fff'),False,points,int(kw.get('width',1)))
    def create_text(self,x,y,**kw):
        spec=kw.get('font',('Segoe UI',11)); size=round(spec[1]*1.2)
        key=(size,'bold' in spec)
        if key not in self.fonts:
            path=pg.font.match_font('segoeui,dejavusans,arial',bold=key[1])
            self.fonts[key]=pg.font.Font(path,size)
        font=self.fonts[key]; lines=str(kw.get('text','')).split('\n')
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
