"""Validate camera math, 3D frame mapping, synchronization and complete decoding."""
import json
import math
import subprocess
from pathlib import Path
from geometry import point,project,state

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'


def main():
    records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
    timeline=json.loads((OUT/'render_timeline.json').read_text())
    cues=json.loads((OUT/'caption_timing.json').read_text())
    mapping=json.loads((OUT/'blender/frame_map.json').read_text())
    duration=records[-1]['end'];n=round(duration*30)
    assert len(records)==len(timeline)==len(cues)==30 and len(mapping)==n
    drift=max(abs(a[k]-b[k]) for a,b in zip(records,timeline) for k in ('start','end'))
    assert drift<1/30,drift
    for i,c in enumerate(cues):
        assert records[i]['start']<=c['start']<c['end']<=records[i]['end']
        if i:assert cues[i-1]['end']<=c['start']
    for z in [1.,2.,2.5]:
        assert max(abs(a-b) for a,b in zip(project(point(z)),(440.,300.)))<1e-10
        assert abs(math.sqrt(sum(x*x for x in point(z)))/math.sqrt(1.05)-z)<1e-10
    assert point(2)==(.4,.2,2)
    for f,idx in enumerate(mapping,1):
        assert (idx is not None)==state(f,records)['visible']
    result={}
    for name in ['pixel_depth_manim_ko.mp4','pixel_depth_blender_ko.mp4','pixel_depth_blender_clean_ko.mp4']:
        file=OUT/name
        info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(file)]))
        v=next(x for x in info['streams'] if x['codec_type']=='video');a=next(x for x in info['streams'] if x['codec_type']=='audio')
        assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'])==(1920,1080,'30/1','h264')
        assert a['codec_name']=='aac' and a['sample_rate']=='48000'
        assert int(v['nb_frames'])==n and len(info['chapters'])==10
        assert abs(float(v['duration'])-duration)<1/30
        assert abs(float(a['duration'])-duration)<.1
        decode=subprocess.run(['ffmpeg','-v','error','-i',str(file),'-f','null','-'],capture_output=True,text=True)
        assert decode.returncode==0 and not decode.stderr,decode.stderr
        result[name]=info
    result['checks']=dict(full_decode='passed',duration=duration,frames=n,chapters=10,captions=30,
        narration_drift_seconds=drift,whisper_timed_cues=sum(c['timing_source']=='whisper' for c in cues),
        xyz=point(2),range=math.sqrt(4.2),reprojection='passed')
    (OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result['checks'],indent=2))


if __name__=='__main__':main()
