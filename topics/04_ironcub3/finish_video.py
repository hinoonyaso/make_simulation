"""Composite trace-driven Blender views into the narrated Manim presentation."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'

def run(args):subprocess.run(args,check=True)
def ass_time(t):
    cs=round(t*100);h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02d}:{s:02d}.{cs:02d}'
def header(w,h,size,margin,font='NanumGothic',align=2):
    return f'''[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00432D20,&H00432D20,0,0,0,0,100,100,0,0,3,7,0,{align},30,30,{margin},1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
def event(start,end,text):return f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Main,,0,0,0,,{text}\n'

def main():
    doc=json.loads((ROOT/'storyboard.json').read_text())
    records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
    sim=json.loads((OUT/'simulation.json').read_text())
    cues=json.loads((OUT/'caption_timing.json').read_text())
    timeline=json.loads((OUT/'render_timeline.json').read_text())
    duration=records[-1]['end']
    starts=[next(r['start'] for r in records if r['chapter']==c) for c in range(9)]
    for c,row in enumerate(timeline):assert abs(row['start']-starts[c])<.04
    sub=header(1920,1080,34,30)
    sub+=''.join(event(c['start'],c['end'],c['caption']) for c in cues)
    (OUT/'subtitles.ko.ass').write_text(sub)
    for mode in ['nominal','mismatch']:
        target=OUT/'blender'/f'{mode}.mp4'
        telemetry=header(900,560,22,16,font='Liberation Sans',align=8)
        for frame in range(361):
            row=sim[mode]['frames'][round(frame*100/30)]
            text=f"t = {row['t']:05.2f} s   |   x = {row['x']:.2f} m   |   z = {row['z']:.2f} m   |   pitch = {row['pitch']*180/3.141592653589793:+.2f} deg"
            telemetry+=event(frame/30,(frame+1)/30,text)
        path=OUT/'blender'/f'{mode}_telemetry.ass';path.write_text(telemetry)
        if not target.exists():
            run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(OUT/'blender'/mode/'%04d.png'),
                '-vf',f'ass={path}','-c:v','libx264','-crf','17','-preset','fast','-pix_fmt','yuv420p','-threads','4',str(target)])
    meta=';FFMETADATA1\ntitle='+doc['title']+'\nlanguage=kor\n'
    for c,ch in enumerate(doc['chapters']):
        end=starts[c+1] if c<8 else duration
        meta+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(starts[c]*1000)}\nEND={round(end*1000)}\ntitle={ch['title']}\n"
    (OUT/'chapters.ffmeta').write_text(meta)
    exp=[r for r in records if r['chapter']==6]
    pre=exp[0]['duration'];end=starts[7];length=end-starts[6]
    filters=[
        '[1:v]scale=1000:622,setsar=1[hero]',
        f"[0:v][hero]overlay=60:255:enable='lt(t,{starts[2]})':eof_action=pass[v1]",
        f'[2:v]tpad=start_mode=clone:start_duration={pre}:stop_mode=clone:stop_duration={length},trim=duration={length},setpts=PTS+{starts[6]}/TB[left]',
        f'[3:v]tpad=start_mode=clone:start_duration={pre}:stop_mode=clone:stop_duration={length},trim=duration={length},setpts=PTS+{starts[6]}/TB[right]',
        f"[v1][left]overlay=40:260:enable='between(t,{starts[6]},{end-1/30})':eof_action=pass[v2]",
        f"[v2][right]overlay=980:260:enable='between(t,{starts[6]},{end-1/30})':eof_action=pass[v3]",
        f"[v3]ass={OUT/'subtitles.ko.ass'}[v]",
        '[4:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]']
    script=OUT/'composite.filter';script.write_text(';\n'.join(filters))
    run(['ffmpeg','-hide_banner','-y','-i',str(ROOT/'media/videos/lesson/1080p30/FlyingHumanoid.mp4'),
        '-loop','1','-framerate','30','-i',str(OUT/'blender/nominal/0000.png'),
        '-i',str(OUT/'blender/nominal.mp4'),'-i',str(OUT/'blender/mismatch.mp4'),
        '-i',str(OUT/'narration.wav'),'-i',str(OUT/'chapters.ffmeta'),
        '-filter_complex_threads','2','-filter_complex_script',str(script),
        '-map','[v]','-map','[a]','-map_metadata','5','-map_chapters','5','-t',str(duration),
        '-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-threads','4',
        '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',
        str(OUT/'ironcub3_education_ko.mp4')])
    (OUT/'composition_timeline.json').write_text(json.dumps(dict(duration=duration,
        experiment_start=starts[6],play_start=starts[6]+pre,simulation_duration=12.,
        experiment_end=end,holds='First state before playback; final state after 12s; no accelerated simulation'),indent=2))
    desc='iRonCub 3 논문의 핵심을 추력, 회전 모멘트, 모델 예측 제어(MPC), 직접 제작한 3D 시뮬레이션으로 설명합니다.\n\n'
    for c,ch in enumerate(doc['chapters']):
        t=int(starts[c]+1e-6);desc+=f"{t//60:02d}:{t%60:02d} {ch['title']}\n"
    desc+='\n이 영상의 3D 로봇과 비교 실험은 교육용 축소 모델입니다. 연구팀의 실제 시험 영상이나 제어기 재현이 아닙니다. 50 kg 강체, 평면 운동, 이상적인 상태 피드백, 1차 추력 지연을 가정하며 관절·UKF·접촉·열유동은 구현하지 않았습니다. 논문의 제트 모델은 비선형 2차 모델입니다.\n'
    for mode,label in [('nominal','모델 일치'),('mismatch','추력 모델 불일치')]:
        m=sim[mode]['metrics'];desc+=f"자체 12초 실험 / {label}: 위치 RMSE {m['position_rmse_m']*100:.2f} cm, 최대 기울기 {m['max_pitch_deg']:.2f}도\n"
    desc+='수치는 실제 iRonCub의 성능이 아닙니다. 비교 실험은 공중에서 시작하며, 제어기의 예측 τ=0.35초는 동일하고 실제 엔진 모델 τ만 0.35/0.77초로 다릅니다.\n\n한국어 합성 음성 및 Whisper 기반 자막 정렬을 사용했습니다.\n\n논문·공식 자료\n'+'\n'.join(doc['sources'])+'\n\n#iRonCub #로봇 #MPC #PhysicalAI #시뮬레이션\n'
    (OUT/'youtube_description.txt').write_text(desc)
    pub=ROOT/'publish';pub.mkdir(exist_ok=True)
    package=dict(video='../output/ironcub3_education_ko.mp4',title=doc['title'],description=desc,
        privacy='public',channel_id='UCKT_GQPU4i_wmtE-b_6wa8A',captions='../output/subtitles.ko.srt',
        caption_language='ko',thumbnail='../output/thumbnail.png',made_for_kids=False,
        tags=['iRonCub','MPC','Flying Humanoid','Physical AI','로봇','Manim','Blender'])
    (pub/'package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
