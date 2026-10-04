"""Combine the Blender animation, Manim formulas and existing Korean audio/captions."""
import json
import subprocess
from itertools import groupby
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
BLEND=OUT/'blender'
FPS=30


def run(*cmd):
    subprocess.run(cmd,check=True,cwd=ROOT)


def main():
    frame_map=json.loads((BLEND/'frame_map.json').read_text())
    previous=0
    frames=[]
    for index in frame_map:
        if index is not None:previous=index
        frames.append(previous)
    concat='ffconcat version 1.0\n'
    for index,group in groupby(frames):
        count=sum(1 for _ in group)
        image=BLEND/'frames'/f'{index:05d}.png'
        if not image.is_file():raise FileNotFoundError(image)
        concat+=f"file '{image.as_posix()}'\noption framerate 30\nduration {count/FPS:.12f}\n"
    concat+=f"file '{(BLEND/'frames'/f'{frames[-1]:05d}.png').as_posix()}'\noption framerate 30\n"
    (BLEND/'frames.ffconcat').write_text(concat)
    strip=BLEND/'robot_3d_view.mp4'
    run('ffmpeg','-hide_banner','-y','-safe','0','-f','concat','-i',str(BLEND/'frames.ffconcat'),
        '-vf','fps=30','-frames:v',str(len(frame_map)),'-c:v','libx264','-preset','fast','-crf','16',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(strip))
    original=OUT/'robot_manipulator_clean_ko.mp4'
    records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
    start=records[40]['start']-1e-6;end=records[44]['start']-1e-6
    enable=f'lt(t,{start:.8f})+gte(t,{end:.8f})'
    graph=f"[0:v]drawbox=x=20:y=202:w=930:h=695:color=0xF7F9FC:t=fill:enable='{enable}'[base]"
    graph+=f";[base][1:v]overlay=x=35:y=215:enable='{enable}':eof_action=repeat[view]"
    # The viewport label communicates the modeling plane, not implementation details.
    font='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    graph+=f";[view]drawtext=fontfile={font}:text='2R ROBOT / XY PLANE':fontsize=20:fontcolor=0x65738A:x=53:y=228:box=1:boxcolor=0xF7F9FC@0.9:boxborderw=6:enable='{enable}'[toplabel]"
    graph+=f";[toplabel]drawtext=fontfile={font}:text='회전축 방향 +Z  /  운동 평면 XY':fontsize=20:fontcolor=0x65738A:x=53:y=865:box=1:boxcolor=0xF7F9FC@0.9:boxborderw=6:enable='{enable}'[labeled]"
    outputs=[('robot_manipulator_blender_ko.mp4',True),('robot_manipulator_blender_clean_ko.mp4',False)]
    for filename,captioned in outputs:
        fg=graph+(f';[labeled]ass={OUT / "subtitles.ko.ass"}[final]' if captioned else ';[labeled]null[final]')
        run('ffmpeg','-hide_banner','-y','-i',str(original),'-i',str(strip),'-filter_complex',fg,
            '-map','[final]','-map','0:a:0','-map_metadata','0','-map_chapters','0',
            '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-r','30',
            '-frames:v',str(len(frame_map)),'-c:a','copy','-movflags','+faststart',str(OUT/filename))
    description=(OUT/'youtube_description.txt').read_text()
    description=description.replace('로봇팔은 좌표를 어떻게 움직임으로 바꿀까?','3D 로봇팔로 이해하는 좌표와 움직임')
    description=description.replace('2관절 평면 로봇팔의 움직임을 수식과 함께 살펴봅니다.',
        'Blender로 시각화한 2관절 로봇팔과 Manim 수식을 함께 살펴봅니다. 운동 모델은 XY 평면의 2R 기구학이며, 입체 모델은 링크 두께와 회전축을 보여주기 위한 표현입니다.')
    (OUT/'youtube_description_blender.txt').write_text(description)
    print('Blender + Manim video package complete.')


if __name__=='__main__':main()
