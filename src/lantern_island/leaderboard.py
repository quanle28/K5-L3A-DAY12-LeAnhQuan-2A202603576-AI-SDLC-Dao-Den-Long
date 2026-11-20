"""Validated, stable top10 local scoreboard. Never reads game renderer/settings."""
from datetime import datetime,timezone
import json
from pathlib import Path
import time
import unicodedata
from .storage import data_dir


def valid_name(value):
    if not isinstance(value,str): return False
    name=unicodedata.normalize('NFC',value)
    return 3<=len(name)<=12 and all(c.isalnum() or c=='_' for c in name)


def timestamp(value):
    if not isinstance(value,str): raise ValueError('achieved_at must be ISO8601 with timezone')
    try: result=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError: raise ValueError('invalid achieved_at')
    if result.tzinfo is None or result.utcoffset() is None: raise ValueError('achieved_at requires timezone')
    return result


def validate_entry(entry):
    if not isinstance(entry,dict) or set(entry)!={'name','score','nights_won','achieved_at','seed'}: raise ValueError('invalid entry fields')
    if not valid_name(entry['name']): raise ValueError('name must be 3–12 letters/digits/underscore')
    if type(entry['score']) is not int or entry['score']<0: raise ValueError('score must be nonnegative integer')
    if type(entry['nights_won']) is not int or not 0<=entry['nights_won']<=3: raise ValueError('nights_won must be0..3')
    if type(entry['seed']) is not int: raise ValueError('seed must be integer')
    timestamp(entry['achieved_at'])
    return dict(entry,name=unicodedata.normalize('NFC',entry['name']))


def sorted_entries(entries):
    clean=[validate_entry(e) for e in entries]
    return sorted(clean,key=lambda e:(-e['score'],timestamp(e['achieved_at']).astimezone(timezone.utc)))[:10]


class Leaderboard:
    def __init__(self,path=None): self.path=Path(path) if path else data_dir()/'leaderboard.json'; self.warning=''
    def entries(self):
        if not self.path.exists(): return []
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data,dict) or not isinstance(data.get('entries'),list): raise ValueError('invalid board format')
            self.warning=''; return sorted_entries(data['entries'])
        except (OSError,ValueError,TypeError,KeyError) as error:
            self.warning='Không đọc được tệp điểm: '+str(error)
            return []
    def add(self,name,score,nights_won,seed,achieved_at=None):
        entry=validate_entry(dict(name=name,score=score,nights_won=nights_won,seed=seed,
                                  achieved_at=achieved_at or datetime.now(timezone.utc).isoformat()))
        old=self.entries()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        if self.warning and self.path.exists():
            backup=self.path.with_name(self.path.name+'.corrupt-'+str(time.time_ns()))
            self.path.replace(backup)
        board=sorted_entries(old+[entry]); tmp=self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(dict(entries=board),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        tmp.replace(self.path); self.warning=''; return board
    def export(self,path):
        entries=self.entries()
        if self.warning: raise ValueError(self.warning)
        Path(path).write_text(json.dumps(dict(entries=entries),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
