"""Export the exact Scene drawing commands to SVG for offscreen visual review.

This is a renderer export, not a desktop screenshot or interactive-play evidence.
"""
import html
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.lantern_island.model import Game
from src.lantern_island.view import Scene


class SvgCanvas:
    def __init__(self,w=1152,h=760): self.w,self.h,self.parts=w,h,[]
    def delete(self,*args): self.parts=[]
    def attributes(self,kw):
        color=kw.get("fill","none") or "none"
        stroke=kw.get("outline","") or "none"
        return 'fill="%s" stroke="%s" stroke-width="%s"'%(color,stroke,kw.get("width",1))
    def create_rectangle(self,x1,y1,x2,y2,**kw):
        self.parts.append('<rect x="%s" y="%s" width="%s" height="%s" %s/>'%(x1,y1,x2-x1,y2-y1,self.attributes(kw)))
    def create_oval(self,x1,y1,x2,y2,**kw):
        self.parts.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" %s/>'%((x1+x2)/2,(y1+y2)/2,(x2-x1)/2,(y2-y1)/2,self.attributes(kw)))
    def create_polygon(self,*coords,**kw):
        self.parts.append('<polygon points="%s" %s/>'%(' '.join('%s,%s'%(x,y) for x,y in zip(coords[::2],coords[1::2])),self.attributes(kw)))
    def create_line(self,*coords,**kw):
        self.parts.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s"/>'%(' '.join('%s,%s'%(x,y) for x,y in zip(coords[::2],coords[1::2])),kw.get('fill','#fff'),kw.get('width',1)))
    def create_text(self,x,y,**kw):
        font=kw.get('font',('sans-serif',11))
        lines=kw.get('text','').split('\n')
        anchor='start' if kw.get('anchor')=='w' else 'middle'
        for i,line in enumerate(lines):
            self.parts.append('<text x="%s" y="%s" fill="%s" text-anchor="%s" dominant-baseline="central" font-family="Segoe UI,DejaVu Sans,sans-serif" font-size="%s" font-weight="%s">%s</text>'%(x,y+(i-(len(lines)-1)/2)*font[1]*1.7,kw.get('fill','#fff'),anchor,font[1]*1.2,'bold' if 'bold' in font else 'normal',html.escape(line)))
    def save(self,path):
        Path(path).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>'%(self.w,self.h,self.w,self.h,'\n'.join(self.parts)),encoding='utf-8')


def main():
    target=ROOT/'docs/proof/phase-1'
    target.mkdir(parents=True,exist_ok=True)
    for name,scenario,yaw in [('scene-start',None,0),('scene-lit',{'lanterns':[{'id':'L1','lit':True},{'id':'L2','lit':True}]},45)]:
        canvas=SvgCanvas()
        Scene(canvas).draw(Game(12,scenario),yaw,1152,760,started=True)
        canvas.save(target/(name+'.svg'))
    print('Exported two offscreen frames from the same renderer used by the desktop game.')


if __name__=='__main__': main()
