"""Frame-exact FFmpeg composition for the Blender/Manim pipeline."""
import json
import subprocess
from itertools import groupby
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'

def run(*args): subprocess.run(args,check=True,cwd=ROOT)

def ass_time(t):
    cs=round(t*100);h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'

def subtitles(timeline):
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Korean,NanumGothic,36,&H00FFFFFF,&H00FFFFFF,&H50243247,&H50243247,0,0,0,0,100,100,0,0,3,9,0,2,100,100,32,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[]
    for b in timeline['beats']:
        caption=b['caption'].replace('\n',r'\N')
        lines.append(f"Dialogue: 0,{ass_time(b['start']+.25)},{ass_time(b['start']+.25+b['speech_duration'])},Korean,,0,0,0,,{caption}")
    (OUT/'subtitles.ko.ass').write_text(header+'\n'.join(lines)+'\n')

def main():
    timeline=json.loads((OUT/'timeline.json').read_text())
    frame_map=json.loads((OUT/'blender/frame_map.json').read_text())
    assert len(frame_map)==timeline['frames']
    previous=next(i for i in frame_map if i is not None)
    indices=[]
    for i in frame_map:
        if i is not None: previous=i
        indices.append(previous)
    lines=['ffconcat version 1.0']
    for index, group in groupby(indices):
        count=sum(1 for _ in group)
        path=OUT/'blender/frames'/f'{index:05d}.png'
        assert path.is_file(),path
        lines.extend([f"file '{path.as_posix()}'",'option framerate 30',f'duration {count/30:.12f}'])
    path=OUT/'blender/frames'/f'{indices[-1]:05d}.png'
    lines.extend([f"file '{path.as_posix()}'",'option framerate 30'])
    concat=OUT/'blender/frames.ffconcat';concat.write_text('\n'.join(lines)+'\n')
    strip=OUT/'blender/viewport.mp4'
    run('ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(concat),
        '-vf','fps=30','-frames:v',str(timeline['frames']),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(strip))
    subtitles(timeline)
    ranges=[]
    for scene,group in groupby(timeline['beats'],lambda b:b['scene']):
        beats=list(group)
        if beats[0]['tool']=='B': ranges.append(f"gte(t,{beats[0]['start']:.10f})*lt(t,{beats[-1]['end']:.10f})")
    enable='+'.join(ranges)
    fg=f"[0:v][1:v]overlay=60:190:enable='{enable}'[view];[view]ass={OUT/'subtitles.ko.ass'}[final]"
    titles=['3축 로봇팔','한 링크의 좌표','두 링크와 누적각','3차원으로 확장','변환행렬','정기구학 요약']
    metadata=[';FFMETADATA1','title=로봇팔은 관절 각도로 손의 위치를 어떻게 계산할까?','comment=Ideal kinematics; Blender and Manim; Korean synthetic narration']
    for scene,group in groupby(timeline['beats'],lambda b:b['scene']):
        beats=list(group)
        metadata.extend(['[CHAPTER]','TIMEBASE=1/30',f"START={beats[0]['start_frame']}",f"END={beats[-1]['end_frame']}",f'title={titles[scene-1]}'])
    meta=OUT/'chapters.ffmetadata';meta.write_text('\n'.join(metadata)+'\n')
    run('ffmpeg','-hide_banner','-loglevel','warning','-y','-i',str(OUT/'manim/lesson.mp4'),'-i',str(strip),
        '-i',str(OUT/'narration.wav'),'-i',str(meta),'-filter_complex',fg,'-map','[final]','-map','2:a:0',
        '-map_metadata','3','-map_chapters','3','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
        '-r','30','-frames:v',str(timeline['frames']),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar','48000',
        '-c:a','aac','-b:a','192k','-t',str(timeline['duration']),'-movflags','+faststart',str(OUT/'EP01_3DOF_Forward_Kinematics_KO.mp4'))

if __name__=='__main__':main()
