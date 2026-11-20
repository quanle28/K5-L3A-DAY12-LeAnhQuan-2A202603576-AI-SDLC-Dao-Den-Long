"""Campaign totals and persistent, validated user settings, independent of GUI."""
import json
from pathlib import Path
from .storage import data_dir

DEFAULT_BINDINGS=dict(move_up=['w','up'],move_down=['s','down'],move_left=['a','left'],move_right=['d','right'],
                      jump=['space'],dash=['left shift','right shift'],interact=['e'],pulse=['f'],pause=['p','escape'])
ACTION_LABELS=dict(move_up='Tiến',move_down='Lùi',move_left='Trái',move_right='Phải',jump='Nhảy',dash='Lướt',interact='Tương tác',pulse='Tỏa sáng',pause='Tạm dừng')


def validate_bindings(data):
    if not isinstance(data,dict) or set(data)!=set(DEFAULT_BINDINGS): raise ValueError('missing binding actions')
    result={}; used=set()
    for action,keys in data.items():
        if not isinstance(keys,list) or not keys or any(not isinstance(k,str) or not 1<=len(k)<=24 for k in keys): raise ValueError('invalid key list')
        keys=[k.lower() for k in keys]
        if len(set(keys))!=len(keys) or any(k in used for k in keys): raise ValueError('duplicate key binding')
        used.update(keys); result[action]=keys
    return result


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
        self.path=Path(path) if path else data_dir()/'settings.json'
        self.volume=.5; self.sensitivity=.25; self.colorblind=False
        self.reduced_motion=False; self.large_text=False
        self.bindings={k:list(v) for k,v in DEFAULT_BINDINGS.items()}
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            volume,sensitivity=data['volume'],data['sensitivity']
            if type(volume) in (float,int) and type(sensitivity) in (float,int) and 0<=volume<=1 and .05<=sensitivity<=1:
                self.volume,self.sensitivity=volume,sensitivity
            if type(data.get('colorblind',False)) is bool: self.colorblind=data.get('colorblind',False)
            for key in ('reduced_motion','large_text'):
                if type(data.get(key,False)) is bool: setattr(self,key,data.get(key,False))
            if 'bindings' in data: self.bindings=validate_bindings(data['bindings'])
        except (OSError,ValueError,KeyError,TypeError): pass
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(dict(volume=self.volume,sensitivity=self.sensitivity,colorblind=self.colorblind,
                                      reduced_motion=self.reduced_motion,large_text=self.large_text,bindings=self.bindings))+'\n',encoding='utf-8')
        tmp.replace(self.path)
    def rebind(self,action,key):
        if action not in ACTION_LABELS: raise ValueError('unknown action')
        key=key.lower()
        for other,keys in self.bindings.items():
            if other!=action and key in keys: raise ValueError('Phím %s đang dùng cho %s'%(key.upper(),ACTION_LABELS[other]))
        candidate={k:list(v) for k,v in self.bindings.items()}; candidate[action]=[key]
        self.bindings=validate_bindings(candidate); self.save()
    def restore_bindings(self):
        self.bindings={k:list(v) for k,v in DEFAULT_BINDINGS.items()}; self.save()
    def key_label(self,action):
        return self.bindings[action][0].upper().replace('LEFT SHIFT','SHIFT').replace('RIGHT SHIFT','SHIFT').replace('ESCAPE','ESC')
