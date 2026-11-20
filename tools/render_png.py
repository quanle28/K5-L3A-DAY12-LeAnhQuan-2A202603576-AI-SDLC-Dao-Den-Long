"""Optional QA export: pip install Pillow --target .qa; not a game dependency."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'.qa'))
from PIL import Image, ImageDraw, ImageFont
from src.lantern_island.model import Game
from src.lantern_island.view import Scene


class ImageCanvas:
    def delete(self,*args):
        self.image=Image.new('RGB',(1152,760))
        self.draw=ImageDraw.Draw(self.image)
    def create_rectangle(self,*coords,**kw): self.draw.rectangle(coords,fill=kw.get('fill'),outline=kw.get('outline') or None,width=int(kw.get('width',1)))
    def create_oval(self,*coords,**kw): self.draw.ellipse(coords,fill=kw.get('fill'),outline=kw.get('outline') or None)
    def create_polygon(self,*coords,**kw): self.draw.polygon(list(zip(coords[::2],coords[1::2])),fill=kw.get('fill'))
    def create_line(self,*coords,**kw): self.draw.line(list(zip(coords[::2],coords[1::2])),fill=kw.get('fill'),width=int(kw.get('width',1)))
    def create_text(self,x,y,**kw):
        spec=kw.get('font',('Segoe UI',11))
        name='segoeuib.ttf' if 'bold' in spec else 'segoeui.ttf'
        try: font=ImageFont.truetype('C:/Windows/Fonts/'+name,round(spec[1]*1.2))
        except OSError: font=ImageFont.truetype('DejaVuSans.ttf',round(spec[1]*1.2))
        self.draw.multiline_text((x,y),kw.get('text',''),font=font,fill=kw.get('fill','#ffffff'),anchor='lm' if kw.get('anchor')=='w' else 'mm',align='center',spacing=8)


if __name__=='__main__':
    for name,scenario,yaw in [('scene-start',None,0),('scene-lit',{'lanterns':[{'id':'L1','lit':True},{'id':'L2','lit':True}]},45)]:
        canvas=ImageCanvas()
        Scene(canvas).draw(Game(12,scenario),yaw,1152,760,started=True)
        canvas.image.save(ROOT/('docs/proof/phase-1/'+name+'.png'))
    print('PNG exports saved. These are offscreen scene renders, not desktop screenshots.')
