"""Campaign totals and persistent, validated user settings, independent of GUI."""
import json
from pathlib import Path


class Campaign:
    def __init__(self): self.night=1; self.scores={}
    @property
    def total(self): return sum(self.scores.values())
    def complete(self,game):
        if game.state!='won': return False
        self.scores[game.night]=game.score
        return True
    def next(self):
        if self.night not in self.scores: return False
        if self.night<3: self.night+=1; return True
        return False


class Settings:
    def __init__(self,path=None):
        self.path=Path(path) if path else Path.home()/'.lantern_island'/'settings.json'
        self.volume=.5; self.sensitivity=.25
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            volume,sensitivity=data['volume'],data['sensitivity']
            if type(volume) in (float,int) and type(sensitivity) in (float,int) and 0<=volume<=1 and .05<=sensitivity<=1:
                self.volume,self.sensitivity=volume,sensitivity
        except (OSError,ValueError,KeyError,TypeError): pass
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(dict(volume=self.volume,sensitivity=self.sensitivity))+'\n',encoding='utf-8')
        tmp.replace(self.path)
