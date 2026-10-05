"""Assemble a short studio hook and persistent map reasoning at measured narration lengths."""
import json
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'output'
FPS=30

def run(args):subprocess.run([str(a) for a in args],check=True)
def duration(p):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)]))
def main():
    manifest=HERE/'visual_manifest.json';doc=json.loads(manifest.read_text());beats=doc['beats']
    source=HERE/'../output/moving_obstacle_ko.mp4'
    segments=[];intro=beats[0]['sec'];lengths=[3.,3.,intro-6.]
    for i,((a,b),target_sec) in enumerate(zip([(44.,47.),(52.,54.),(58.,60.)],lengths)):
        target=OUT/f'opening_{i}.mp4';segments.append(target)
        run(['ffmpeg','-v','error','-y','-ss',a,'-t',b-a,'-i',source,'-an','-sn',
             '-vf',f'setpts={target_sec/(b-a):.12f}*(PTS-STARTPTS),fps=30,tpad=stop_mode=clone:stop_duration=0.2',
             '-frames:v',round(target_sec*FPS),'-c:v','libx264','-threads','2','-preset','fast','-crf','17','-pix_fmt','yuv420p',target])
    reasoning=OUT/'final_render/videos/reasoning_scene/1080p30/MovingObstacleReasoning.mp4'
    expected=sum(b['sec'] for b in beats[1:])
    drift=duration(reasoning)-expected
    if abs(drift)>.12: raise RuntimeError(f'Manim timing drift {drift:.3f}s; inspect before assembly')
    print(f'Manim timing drift: {drift:.3f}s',flush=True)
    segments.append(reasoning)
    concat=OUT/'picture_concat.txt';concat.write_text(''.join(f"file '{p.resolve().as_posix()}'\n" for p in segments))
    picture=OUT/'picture.mp4'
    inputs=[]
    for segment in segments: inputs+=['-i',segment]
    chains=';'.join(f'[{i}:v]setpts=PTS-STARTPTS,setsar=1[v{i}]' for i in range(len(segments)))
    chains+=';' + ''.join(f'[v{i}]' for i in range(len(segments))) + f'concat=n={len(segments)}:v=1:a=0[v]'
    run(['ffmpeg','-v','error','-y',*inputs,'-filter_complex',chains,'-map','[v]','-an','-sn',
         '-c:v','libx264','-threads','2','-preset','fast','-crf','17','-pix_fmt','yuv420p','-r',FPS,picture])
    total=sum(b['sec'] for b in beats)
    final=OUT/'moving_obstacle_ko_v3.mp4'
    run(['ffmpeg','-v','error','-y','-i',picture,'-i',OUT/'narration.wav','-i',OUT/'subtitles.ko.srt',
         '-filter_complex','[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]',
         '-map','0:v:0','-map','[a]','-map','2:s:0','-t',f'{total:.6f}',
         '-c:v','copy','-c:a','aac','-b:a','192k','-c:s','mov_text','-metadata:s:s:0','language=kor','-movflags','+faststart',final])
    now=0.
    for beat in beats:
        beat['media']='output/moving_obstacle_ko_v3.mp4';beat['media_in']=round(now,6);now+=beat['sec'];beat['media_out']=round(now,6)
    manifest.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(f'FINAL {final} {total:.2f}s',flush=True)
if __name__=='__main__':main()
