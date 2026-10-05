"""Mux the measured beat contract; critical excerpt selects IDs, never copies beat definitions."""
import argparse
import json
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'output'

def run(args):subprocess.run([str(a) for a in args],check=True)
def duration(path):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)]))
def main(critical):
    mp=HERE/'visual_manifest.json';doc=json.loads(mp.read_text());records=json.loads((HERE/'assets/audio/manifest.json').read_text())
    ids=doc['critical_excerpt']['beat_ids'] if critical else [b['id'] for b in doc['beats']]
    selected=[r for r in records if r['beat'] in ids]
    start=selected[0]['start'];end=selected[-1]['end'];seconds=end-start
    if critical:
        picture=OUT/'critical_render/videos/discovery_scene/540p30/CriticalInference.mp4'
        wav=OUT/'critical_narration.wav'
        run(['ffmpeg','-v','error','-y','-i',OUT/'narration.wav','-af',f'atrim=start={start:.9f}:end={end:.9f},asetpts=PTS-STARTPTS','-ar','48000',wav])
        final=OUT/'critical_excerpt.mp4'
        cues=[{**c,'start':c['start']-start,'end':c['end']-start} for c in json.loads((OUT/'caption_timing.json').read_text()) if c['start']>=start and c['end']<=end]
        cp=OUT/'critical_caption_timing.json';cp.write_text(json.dumps(cues,ensure_ascii=False,indent=2)+'\n')
        def stamp(t):
            ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
        subtitles=OUT/'critical.ko.srt';subtitles.write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['caption']}" for i,c in enumerate(cues))+'\n')
    else:
        picture=OUT/'final_render/videos/discovery_scene/1080p30/ObstacleDiscovery.mp4'
        wav=OUT/'narration.wav';final=OUT/'moving_obstacle_ko_v4.mp4';subtitles=OUT/'subtitles.ko.srt'
    drift=duration(picture)-seconds
    if abs(drift)>.30:raise ValueError(f'Inspect timing drift: {drift:.3f}s')
    run(['ffmpeg','-v','error','-y','-i',picture,'-i',wav,'-i',subtitles,
         '-filter_complex','[0:v]tpad=stop_mode=clone:stop_duration=0.3,fps=30[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]',
         '-map','[v]','-map','[a]','-map','2:s:0','-t',f'{seconds:.9f}','-c:v','libx264','-threads','2','-preset','fast','-crf','17','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','192k','-c:s','mov_text','-metadata:s:s:0','language=kor','-movflags','+faststart',final])
    if not critical:
        now=0.
        for b in doc['beats']:
            b['media']=str(final.relative_to(HERE));b['media_in']=round(now,6);now+=b['sec'];b['media_out']=round(now,6)
        mp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    (OUT/('critical_assembly.json' if critical else 'assembly.json')).write_text(json.dumps({'media':str(final.relative_to(HERE)),'beat_ids':ids,'source_start':start,'duration_s':seconds,'render_drift_s':drift},indent=2)+'\n')
    print(f'FINAL {final} {seconds:.2f}s drift={drift:.3f}s',flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--critical',action='store_true');main(ap.parse_args().critical)
