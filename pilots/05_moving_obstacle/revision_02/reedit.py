"""Retiming existing encoded picture to measured narration; keeps source playback order."""
import json
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
FPS=30

def run(args):
    subprocess.run([str(a) for a in args],check=True)

def main():
    path=HERE/'visual_manifest.json'
    doc=json.loads(path.read_text())
    out=HERE/'output'; out.mkdir(exist_ok=True)
    cuts=out/'segments'; cuts.mkdir(exist_ok=True)
    now=0.0; segments=[]
    for b in doc['beats']:
        target=cuts/(b['id']+'.mp4')
        ratio=b['sec']/(b['source_out']-b['source_in'])
        video_filter=f'setpts={ratio:.12f}*(PTS-STARTPTS),fps={FPS},tpad=stop_mode=clone:stop_duration=0.1'
        if b.get('display_label'):
            label=cuts/(b['id']+'.txt'); label.write_text(b['display_label'])
            video_filter+=f',drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf:textfile={label}:fontsize=38:fontcolor=white:borderw=3:bordercolor=black@0.7:x=70:y=65:line_spacing=12'
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',b['source_in'],
             '-t',b['source_out']-b['source_in'],'-i',HERE/b['source_media'],
             '-an','-sn','-vf',video_filter,
             '-frames:v',round(b['sec']*FPS),'-c:v','libx264','-threads','2','-preset','fast','-crf','17',
             '-pix_fmt','yuv420p',target])
        b['media']='output/moving_obstacle_ko_v2.mp4'
        b['media_in']=round(now,6); now+=b['sec']; b['media_out']=round(now,6)
        segments.append(target)
        print(f"Retimed {b['id']}: {b['sec']:.2f}s",flush=True)
    concat=out/'picture_concat.txt'
    concat.write_text(''.join(f"file '{p.as_posix()}'\n" for p in segments))
    picture=out/'picture_v2.mp4'
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',concat,'-c:v','copy',picture])
    final=out/'moving_obstacle_ko_v2.mp4'
    run(['ffmpeg','-v','error','-y','-i',picture,'-i',out/'narration.wav','-i',out/'subtitles.ko.srt',
         '-filter_complex','[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]',
         '-map','0:v:0','-map','[a]','-map','2:s:0','-t',f'{now:.6f}',
         '-c:v','copy','-c:a','aac','-b:a','192k','-c:s','mov_text',
         '-metadata:s:s:0','language=kor','-movflags','+faststart',final])
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(f'FINAL {final} {now:.2f}s',flush=True)
if __name__=='__main__': main()
