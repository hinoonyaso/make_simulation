"""Burn retimed Whisper captions and package the 9:16 short; verify the result."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'


def stamp(t):
    cs=round(t*100);h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'


def main():
    cues=json.loads((OUT/'caption_timing.json').read_text())
    recs=json.loads((ROOT/'assets/audio/manifest.json').read_text())
    timeline=json.loads((OUT/'timeline.json').read_text())
    ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Korean,NanumGothic,54,&H00FFFFFF,&H00FFFFFF,&H00432D20,&H00432D20,0,0,0,0,100,100,0,0,3,12,0,2,110,200,385,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    for c in cues:
        caption=c['caption'].replace('\n',r'\N')
        ass+=f"Dialogue: 0,{stamp(c['start'])},{stamp(c['end'])},Korean,,0,0,0,,{caption}\n"
    (OUT/'subtitles.ko.ass').write_text(ass)
    file=OUT/'qlora_shorts_ko.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(ROOT/'media/videos/short_video/1920p30/QLoRAShort.mp4'),
        '-i',str(OUT/'narration.wav'),'-map','0:v:0','-map','1:a:0','-vf',f"ass={OUT/'subtitles.ko.ass'}",
        '-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','4',
        '-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-metadata:s:a:0','language=kor','-movflags','+faststart',str(file)],check=True)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(file)]))
    v=next(s for s in info['streams'] if s['codec_type']=='video');a=next(s for s in info['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'],v['r_frame_rate'])==(1080,1920,'30/1')
    assert abs(float(v['duration'])-recs[-1]['end'])<1/30
    assert abs(float(a['duration'])-recs[-1]['end'])<.1
    drift=max(abs(r[k]-t[k]) for r,t in zip(recs,timeline) for k in ('start','end'))
    assert drift<1/30
    for i,c in enumerate(cues):
        assert recs[i]['start']<=c['start']<c['end']<=recs[i]['end']
        if i:assert cues[i-1]['end']<=c['start']
    decode=subprocess.run(['ffmpeg','-v','error','-i',str(file),'-f','null','-'],capture_output=True,text=True)
    assert decode.returncode==0 and not decode.stderr
    info['checks']=dict(full_decode='passed',duration=recs[-1]['end'],speed=1.3,captions=8,narration_drift_seconds=drift)
    (OUT/'validation.json').write_text(json.dumps(info,indent=2))
    (OUT/'youtube_description.txt').write_text('QLoRA 핵심 1분 | 4-bit 저장, 고정밀 계산, LoRA 학습\n\n본편의 핵심 8개 발화를 약 1.3배 템포로 재편집했습니다. 7B의 14 GB / 3.5 GB는 가중치 표현만 비교하며, 전체 학습 메모리가 아닙니다. 한국어 합성 내레이션과 Whisper 타이밍을 보정한 자막을 사용했습니다.\n\n#QLoRA #LoRA #LLM #Shorts\n')
    print(json.dumps(info['checks'],indent=2))


if __name__=='__main__':main()
