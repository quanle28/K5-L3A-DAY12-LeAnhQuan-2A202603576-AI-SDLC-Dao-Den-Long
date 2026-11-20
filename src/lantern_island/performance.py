"""Version1.3 performance tools, isolated from the unchanged gameplay CLI."""
import gc
import json
import math
import os
from pathlib import Path
import platform
import random
import sys
import time
from .model import Game,DEFAULT_INPUT,DT,direction,distance

ROOT=Path(__file__).resolve().parents[2]
_process=None


def rss_mb():
    return memory_process().memory_info().rss/(1024*1024)


def memory_process():
    global _process
    sys.path.insert(0,str(ROOT/'.runtime')) if str(ROOT/'.runtime') not in sys.path else None
    import psutil
    if _process is None or _process.pid!=os.getpid(): _process=psutil.Process(os.getpid())
    return _process


def frame_statistics(samples):
    if not samples or any(not math.isfinite(x) or x<=0 for x in samples): raise ValueError('positive finite frame times required')
    values=sorted(samples); n=len(values); k=max(1,math.ceil(.01*n))
    p=(n-1)*.95; lo=math.floor(p); hi=math.ceil(p)
    return dict(avg_fps=1000*n/sum(values),p1_low_fps=1000/(sum(values[-k:])/k),
                frame_ms_p95=values[lo]+(values[hi]-values[lo])*(p-lo),frames=n)


def orbit_camera(seconds):
    angle=math.tau*seconds/15
    return ([30*math.cos(angle),15.,30*math.sin(angle)],[0.,0.,0.])


def benchmark_game(seed):
    rng=random.Random(seed)
    def point():
        a=rng.random()*math.tau; r=math.sqrt(rng.random())*40
        return [r*math.cos(a),0.,r*math.sin(a)]
    shades=[]
    for i in range(200):
        p=point(); p[1]=.8
        shades.append(dict(id='S'+str(i+1),pos=p,state='wander'))
    scenario=dict(random_motes=False,random_shades=False,random_drifters=False,wind_enabled=False,
                  motes=[point() for _ in range(100)],shades=shades,lanterns=[dict(id='L'+str(i),lit=True,fuel=100) for i in (1,2,3)])
    return Game(seed,scenario,1)


def benchmark_step(game):
    # Intentionally isolated: no Game.step(), pickup, contact, spawn, fuel or terminal.
    game.tick+=1; game.sim_tick+=1
    speed=4.
    for shade in game.shades:
        shade['state']='wander'
        game._wander(shade,speed)


def run_benchmark(seed,duration,out,process_started=None,frame_callback=None):
    if not math.isfinite(duration) or duration<=0: raise ValueError('duration must be positive')
    os_start=time.perf_counter()-max(0,time.time()-memory_process().create_time())
    start=min(os_start,process_started) if process_started is not None else os_start
    from .pygame_canvas import pg,PygameCanvas
    from .render import Scene
    pg.display.init(); pg.font.init()
    # Software display has no swap interval; request vsync0 explicitly as well.
    surface=pg.display.set_mode((1280,720),flags=0,vsync=0)
    pg.display.set_caption('Đảo Đèn Lồng · benchmark chuẩn v1.3')
    canvas=PygameCanvas(surface); scene=Scene(canvas); game=benchmark_game(seed)
    scene_start=time.perf_counter(); last_update=scene_start; accumulator=0.
    first_flip=None; measure_start=None; measure_end=None; last_flip=None
    samples=[]; peak=0.; frames_total=0
    try:
        while True:
            begin=time.perf_counter(); elapsed=begin-last_update; last_update=begin
            accumulator+=elapsed
            while accumulator>=DT:
                benchmark_step(game); accumulator-=DT
            for event in pg.event.get():
                if event.type==pg.QUIT: raise RuntimeError('benchmark interrupted by window close')
            scene.draw(game,0,1280,720,camera=orbit_camera(0 if first_flip is None else begin-scene_start),benchmark=True)
            pg.display.flip(); now=time.perf_counter(); frames_total+=1
            if first_flip is None:
                first_flip=now; load_ms=(now-start)*1000
            if measure_start is None and now-first_flip>=3:
                measure_start=now; measure_end=now+duration; last_flip=now
                peak=rss_mb()
            elif measure_start is not None:
                if now>measure_end: break
                samples.append((now-last_flip)*1000); last_flip=now
                peak=max(peak,rss_mb())
            if frame_callback: frame_callback(surface,now-scene_start)
        stats=frame_statistics(samples)
        result=dict(contract_version='1.3',**{k:round(v,4) if isinstance(v,float) else v for k,v in stats.items()},
                    load_ms=round(load_ms,3),peak_mem_mb=round(peak,3),vsync_off=True,
                    renderer='Pygame %s / SDL %s software perspective; shared mesh/sprite LOD renderer'%(pg.version.ver,'.'.join(map(str,pg.get_sdl_version()))),os=platform.platform(),
                    seed=seed,duration_s=duration,warmup_s=3,resolution=[1280,720],windowed=True,
                    scene=dict(night=1,shades=len(game.shades),motes=len(game.motes),lit=sum(l['lit'] for l in game.lanterns),player=game.pos,
                               fuel=[game.fuel(l) for l in game.lanterns[:3]],spawn=False,damage=False,pickup=False,fuel_decay=False,terminal=False,creativity=False),
                    camera='R30,Y15,lookat origin; +X start; XZ CCW; 15 seconds/revolution',rss_method='psutil current RSS sampled each measured frame; MiB',
                    p95_method='linear interpolation (type7)',measurement_wall_s=duration,overshoot_ms=round(max(0,now-measure_end)*1000,3))
        path=Path(out); path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        path.with_suffix('.samples.json').write_text(json.dumps(dict(frame_ms=samples,measurement_duration_s=duration),separators=(',',':'))+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False))
        return result
    finally: pg.quit()


def random_controls(rng,tick,move):
    if tick%30==0:
        angle=rng.random()*math.tau; move=[math.cos(angle),math.sin(angle)]
    return dict(DEFAULT_INPUT,move=move,jump=rng.random()<.05,dash=rng.random()<.03,pulse=rng.random()<.02,interact=rng.random()<.10),move


def run_soak(seed,nights,out):
    if type(nights) is not int or nights<1: raise ValueError('nights must be positive integer')
    started=time.perf_counter(); results=[]; errors=[]; ticks=[]
    game=Game(seed,night=1); gc.collect(); mem_start=rss_mb()
    for i in range(nights):
        night=i%3+1; run_seed=seed+i
        if i: game=Game(run_seed,night=night)
        rng=random.Random(run_seed); move=[0,0]
        try:
            limit=round(game.duration*60)
            for tick in range(limit):
                c,move=random_controls(rng,tick,move); game.step(c)
                if game.state in ('won','lost'): break
            results.append(game.state); ticks.append(game.sim_tick)
        except Exception as error:
            errors.append(dict(index=i,night=night,error=type(error).__name__+': '+str(error)))
            results.append('crashed'); ticks.append(game.sim_tick)
        del game; gc.collect()
    # Reset the last Night to its starting state, in this same process, then sample RSS.
    game=Game(seed+nights-1,night=(nights-1)%3+1); gc.collect(); mem_end=rss_mb()
    data=dict(nights=nights,crashes=len(errors),results=results,mem_start_mb=round(mem_start,4),mem_end_mb=round(mem_end,4),duration_s=round(time.perf_counter()-started,4),
              pid=os.getpid(),seed=seed,seeds=list(range(seed,seed+nights)),night_order=[i%3+1 for i in range(nights)],sim_ticks=ticks,
              rss_method='psutil current RSS /1024² after first load and after final reset+gc; same PID',errors=errors)
    Path(out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data,ensure_ascii=False))
    return data
