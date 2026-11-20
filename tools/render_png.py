"""Offscreen exports from the same Pygame renderer, without a display/audio device."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.lantern_island.pygame_canvas import pg,PygameCanvas
from src.lantern_island.render import Scene
from src.lantern_island.model import Game
from src.lantern_island.maps import PALETTE


def main():
    pg.font.init(); target=ROOT/'docs/proof/phase-3'; target.mkdir(parents=True,exist_ok=True)
    for night in (1,2,3):
        surface=pg.Surface((1280,720)); canvas=PygameCanvas(surface)
        g=Game(12,{'lanterns':[{'id':'L1','lit':True},{'id':'L2','lit':True}]},night)
        Scene(canvas).draw(g,25,1280,720)
        pg.image.save(surface,str(target/('lit-night%d.png'%night)))
    surface=pg.Surface((900,600)); c=PygameCanvas(surface); c.delete('all')
    for i,(name,color) in enumerate(PALETTE.items()):
        x=20+(i%4)*220; y=20+(i//4)*110
        c.create_rectangle(x,y,x+195,y+60,fill=color,outline='')
        c.create_text(x+98,y+80,text=name+' '+color,fill=PALETTE['text'],font=('Segoe UI',11))
    pg.image.save(surface,str(target/'palette.png'))
    print('Offscreen lit-map and exact material palette PNG exports saved (not interactive-play screenshots).')


if __name__=='__main__': main()
