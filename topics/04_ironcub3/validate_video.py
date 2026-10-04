import json,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'

def main():
    video=OUT/'ironcub3_education_ko.mp4'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams',
        '-show_chapters','-of','json',str(video)]))
    records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
    cues=json.loads((OUT/'caption_timing.json').read_text())
    sim=json.loads((OUT/'simulation.json').read_text())
    timeline=json.loads((OUT/'render_timeline.json').read_text())
    duration=records[-1]['end'];vs=next(s for s in probe['streams'] if s['codec_type']=='video')
    audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert (vs['width'],vs['height'],vs['r_frame_rate'])==(1920,1080,'30/1')
    assert abs(float(probe['format']['duration'])-duration)<.10
    assert abs(float(audio['duration'])-duration)<.10
    assert len(probe['chapters'])==9 and len(cues)==len(records)==29
    assert abs(int(vs['nb_frames'])/30-duration)<.04
    for i,cue in enumerate(cues):
        assert 0<=cue['start']<cue['end']<=duration
        if i:assert cues[i-1]['end']<=cue['start']
    for c,row in enumerate(timeline):
        expected=next(r['start'] for r in records if r['chapter']==c)
        assert abs(row['start']-expected)<.04
    for mode in ['nominal','mismatch']:
        frames=sim[mode]['frames']
        errors=np.array([np.hypot(f['x']-f['target'][0],f['z']-f['target'][1]) for f in frames])
        assert np.allclose(errors,[f['error'] for f in frames])
        assert abs(np.sqrt(np.mean(errors**2))-sim[mode]['metrics']['position_rmse_m'])<1e-10
        assert len(list((OUT/'blender'/mode).glob('[0-9][0-9][0-9][0-9].png')))==361
    assert np.allclose([f['target'] for f in sim['nominal']['frames']],
                       [f['target'] for f in sim['mismatch']['frames']])
    saved=json.loads((OUT/'blender/validation.json').read_text());assert len(saved)==2
    subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True)
    report=dict(passed=True,duration_seconds=duration,frames=int(vs['nb_frames']),
        captions=len(cues),chapters=len(probe['chapters']),resolution=[1920,1080],
        decode='complete',model_metrics={m:sim[m]['metrics'] for m in ['nominal','mismatch']},
        saved_blender_trace_check=saved)
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
