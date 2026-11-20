"""Fail a local release gate when actual measurements/proof do not match sources."""
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.lantern_island.performance import frame_statistics

def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))

def main():
    manifest=read('game.contract.json'); bench=read('bench.json'); soak=read('soak.json')
    assert manifest['contract_version']==bench['contract_version']=='1.3'
    assert manifest['bench_cmd'] and manifest['soak_cmd']
    samples=read('bench.samples.json')['frame_ms']; recomputed=frame_statistics(samples)
    for key in ('avg_fps','p1_low_fps','frame_ms_p95','frames'): assert abs(recomputed[key]-bench[key])<.0001,key
    assert bench['avg_fps']>=60 and bench['p1_low_fps']>=30 and bench['load_ms']<=10000
    assert bench['seed']==42 and bench['duration_s']==30 and bench['warmup_s']==3
    assert bench['resolution']==[1280,720] and bench['windowed'] and bench['vsync_off']
    assert bench['scene']['shades']==200 and bench['scene']['motes']==100 and bench['scene']['lit']==3
    assert bench['scene']['player']==[0,0,0] and bench['scene']['fuel']==[100]*3
    assert all(bench['scene'][k] is False for k in ('spawn','damage','pickup','fuel_decay','terminal','creativity'))
    assert soak['crashes']==0 and soak['nights']==10 and len(soak['results'])==10
    assert all(r in ('won','lost') for r in soak['results'])
    assert soak['seeds']==list(range(7,17)) and soak['night_order']==[i%3+1 for i in range(10)]
    assert soak['mem_end_mb']<=1.2*soak['mem_start_mb'] and soak['mem_start_mb']>0
    proof=ROOT/'docs/proof/phase-4'
    verify=read('docs/proof/phase-4/verification.json')
    for name,digest in verify['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,'stale proof '+name
    assert len(verify['scenarios'])==28 and all(c['deterministic'] for c in verify['scenarios'])
    tests=(proof/'tests.txt').read_text(encoding='utf-8')
    assert re.search(r'Ran 96 tests',tests) and tests.rstrip().endswith('OK')
    old=read('docs/proof/phase-4/phase3-regression.json')
    assert len(old['cases'])==28 and all(c['identical'] for c in old['cases'])
    gui=read('docs/proof/phase-4/gui-smoke.json')
    assert len(gui['runs'])==3 and all(r['average_fps']>=30 for r in gui['runs'])
    stress=read('docs/proof/phase-4/renderer-stress.json')
    assert all(r['average_fps']>=30 for r in stress['results'])
    assert (proof/'clean-check.txt').exists()
    video=read('docs/demo/metadata.json'); assert 0<video['duration']<300 and video['size']==[1280,720]
    mp4=ROOT/'docs/demo/demo.mp4'; assert b'ftyp' in mp4.read_bytes()[:32]
    for name in ('README.md','CHANGELOG.md','CREDITS.md','LICENSE','docs/notes/retro.md','docs/release-v1.0.0.md'):
        assert (ROOT/name).stat().st_size>100,name
    report=dict(contract_version='1.3',local_gate='passed',unit_tests=96,deterministic_scenarios=28,phase3_byte_regressions=28,
                benchmark=bench,soak=soak,video_sha256=hashlib.sha256(mp4.read_bytes()).hexdigest(),
                limitations='Local release gate; instructor hardware/hidden tests/human play and listening are not certified.')
    (proof/'release-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: actual benchmark/rawdt, soak,96tests,28regressions,GUI,clean build and MP4; source hashes match.')

if __name__=='__main__': main()
