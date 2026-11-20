"""Strict finite JSON validation for Test Contract input files."""
import math

DEFAULT_INPUT=dict(move=[0,0],cam_yaw_deg=0,jump=False,interact=False,pulse=False,dash=False,pause=False)


def number(value,label,minimum=None,maximum=None):
    if type(value) not in (int,float) or not math.isfinite(value): raise ValueError(label+' must be finite numeric')
    if minimum is not None and value<minimum or maximum is not None and value>maximum: raise ValueError(label+' outside range')
    return value


def integer(value,label,minimum=0,maximum=None):
    if type(value) is not int: raise ValueError(label+' must be an integer')
    return number(value,label,minimum,maximum)


def boolean(value,label):
    if type(value) is not bool: raise ValueError(label+' must be boolean')
    return value


def fields(obj,allowed,label):
    if not isinstance(obj,dict) or set(obj)-set(allowed): raise ValueError(label+' has invalid fields')


def position(value):
    if not isinstance(value,list) or len(value)!=3: raise ValueError('pos must be [x,y,z]')
    return [number(v,'position') for v in value]


def validate_inputs(data):
    fields(data,['frames'],'inputs')
    frames=data.get('frames')
    if not isinstance(frames,list): raise ValueError('frames must be an array')
    previous=-1
    for f in frames:
        fields(f,['tick']+list(DEFAULT_INPUT),'input frame')
        tick=integer(f.get('tick'),'tick')
        if tick<=previous: raise ValueError('input ticks must increase strictly')
        previous=tick
        if 'move' in f:
            if not isinstance(f['move'],list) or len(f['move'])!=2: raise ValueError('move must be [x,z]')
            for v in f['move']: number(v,'move',-1,1)
        if 'cam_yaw_deg' in f: number(f['cam_yaw_deg'],'cam_yaw_deg')
        for k in ('jump','interact','pulse','dash','pause'):
            if k in f: boolean(f[k],k)
    return frames
