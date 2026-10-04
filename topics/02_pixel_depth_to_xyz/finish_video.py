"""Package the Manim lesson, then the Blender + Manim final versions."""
import json
import argparse
import subprocess
from itertools import groupby
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output';BLEND=OUT/'blender'
FONT='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'


def run(*args):subprocess.run(args,check=True,cwd=ROOT)


def ass_time(t):
    cs=round(t*100);h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--compose-only',action='store_true',help='Reuse the existing Manim package and 3D strip')
    args=parser.parse_args()
    records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
    doc=json.loads((ROOT/'storyboard.json').read_text());n=round(records[-1]['end']*30)
    cues=json.loads((OUT/'caption_timing.json').read_text())
    ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Korean,NanumGothic,40,&H00FFFFFF,&H00FFFFFF,&H00432D20,&H00432D20,0,0,0,0,100,100,0,0,3,12,0,2,100,100,78,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    for c in cues:ass+=f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Korean,,0,0,0,,{c['caption']}\n"
    (OUT/'subtitles.ko.ass').write_text(ass)
    chapters=[r for r in records if r['line']==0]
    meta=';FFMETADATA1\ntitle=Pixel + Depth → 3D XYZ\nlanguage=kor\n'
    description='제목: 픽셀과 깊이로 3D 위치를 구하는 법 | 카메라 → pixel → ray → 3D point\n\n'
    description+='Manim의 수식과 Blender의 3D 카메라 장면으로 역투영을 설명합니다. 핀홀 모델, 내부 파라미터, 광학축 깊이 Z, 실제 숫자 예제와 로봇 좌표 변환을 연결합니다.\n\n'
    for ci,r in enumerate(chapters):
        end=chapters[ci+1]['start'] if ci+1<len(chapters) else records[-1]['end']
        meta+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(r['start']*1000)}\nEND={round(end*1000)}\ntitle={doc['chapters'][ci]['title']}\n"
        secs=int(r['start']+1e-7);description+=f"{secs//60:02}:{secs%60:02} {doc['chapters'][ci]['title']}\n"
    (OUT/'chapters.ffmeta').write_text(meta)
    description+='\nX=(u-cx)Z/fx, Y=(v-cy)Z/fy. 예시: fx=fy=600 px, (cx,cy)=(320,240), (u,v)=(440,300), Z=2 m → P=(0.4,0.2,2) m.\n'
    description+='왜곡 보정된 픽셀, skew=0, 해당 영상의 K를 사용합니다. Z는 광학축 성분이며 광선을 따라 잰 거리 R과 다릅니다. 영상 평면은 설명용 가상 평면입니다. 좌표 역투영과 기하 시각화이며 센서 노이즈나 렌즈의 광학 현상을 시뮬레이션한 것은 아닙니다.\n'
    description+='한국어 합성 음성과 Whisper 기반 대본 정렬·교정 자막을 사용했습니다.\n\n참고 자료\n'+'\n'.join(doc['sources'])+'\n\n#컴퓨터비전 #카메라 #Depth #Manim #Blender\n'
    (OUT/'youtube_description.txt').write_text(description)
    (OUT/'narration.ko.txt').write_text('\n\n'.join(ch['title']+'\n'+'\n'.join(line[0] for line in ch['lines']) for ch in doc['chapters']))
    source=ROOT/'media/videos/pixel_depth_video/1080p30/PixelDepthLesson.mp4'
    common=['-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','4',
        '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-metadata:s:a:0','language=kor',
        '-frames:v',str(n),'-movflags','+faststart']
    if not args.compose_only:
        run('ffmpeg','-hide_banner','-y','-i',str(source),'-i',str(OUT/'narration.wav'),'-i',str(OUT/'chapters.ffmeta'),
            '-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2',
            '-vf',f"ass={OUT/'subtitles.ko.ass'}",'-af','loudnorm=I=-16:TP=-1.5:LRA=11',*common,str(OUT/'pixel_depth_manim_ko.mp4'))
    mapping=json.loads((BLEND/'frame_map.json').read_text());prev=0;indices=[]
    for idx in mapping:
        if idx is not None:prev=idx
        indices.append(prev)
    concat='ffconcat version 1.0\n'
    for idx,g in groupby(indices):
        count=sum(1 for _ in g);file=BLEND/'frames'/f'{idx:05}.png'
        assert file.exists(),file
        concat+=f"file '{file.as_posix()}'\noption framerate 30\nduration {count/30:.12f}\n"
    concat+=f"file '{(BLEND/'frames'/f'{indices[-1]:05}.png').as_posix()}'\noption framerate 30\n"
    (BLEND/'frames.ffconcat').write_text(concat)
    strip=BLEND/'camera_3d_view.mp4'
    if not args.compose_only:
        run('ffmpeg','-hide_banner','-y','-safe','0','-f','concat','-i',str(BLEND/'frames.ffconcat'),
            '-vf','fps=30','-frames:v',str(n),'-c:v','libx264','-preset','fast','-crf','16','-threads','4','-pix_fmt','yuv420p',str(strip))
    from geometry import BLENDER_CHAPTERS
    intervals=[]
    for ci in sorted(BLENDER_CHAPTERS):
        r=[r for r in records if r['chapter']==ci]
        intervals.append(f"between(t,{r[0]['start']:.9f},{r[-1]['end']-1e-6:.9f})")
    enable='+'.join(intervals)
    graph=f"[0:v]drawbox=x=35:y=225:w=920:h=670:color=0xF7F9FC:t=fill:enable='{enable}'[cleared]"
    graph+=f";[cleared][1:v]overlay=x=45:y=245:enable='{enable}'[over]"
    graph+=f";[over]drawtext=fontfile={FONT}:text='CAMERA OPTICAL FRAME':fontsize=23:fontcolor=0x65738A:x=65:y=252:box=1:boxcolor=0xF7F9FC:boxborderw=5:enable='{enable}'[v1]"
    er=next(r for r in records if r['chapter']==6 and r['line']==2)
    graph+=f";[v1]drawtext=fontfile={FONT}:text='P = (0.4, 0.2, 2.0) m':fontsize=30:fontcolor=0xED941D:x=215:y=815:box=1:boxcolor=0xF7F9FC:boxborderw=5:enable='between(t,{er['start']:.9f},{er['end']-1e-6:.9f})'[v2]"
    graph+=f";[v2]drawtext=fontfile={FONT}:text='가상 영상 평면 · 광학축 깊이 Z':fontsize=22:fontcolor=0x65738A:x=95:y=861:box=1:boxcolor=0xF7F9FC:boxborderw=4:enable='{enable}'[labeled]"
    for name,captioned in [('pixel_depth_blender_ko.mp4',True),('pixel_depth_blender_clean_ko.mp4',False)]:
        fg=graph+(f";[labeled]ass={OUT/'subtitles.ko.ass'}[final]" if captioned else ';[labeled]null[final]')
        run('ffmpeg','-hide_banner','-y','-i',str(source),'-i',str(strip),'-i',str(OUT/'narration.wav'),'-i',str(OUT/'chapters.ffmeta'),
            '-filter_complex',fg,'-map','[final]','-map','2:a:0','-map_metadata','3','-map_chapters','3',
            '-af','loudnorm=I=-16:TP=-1.5:LRA=11',*common,str(OUT/name))
    print('Pixel + Depth: Manim and Blender upload package complete.',flush=True)


if __name__=='__main__':main()
