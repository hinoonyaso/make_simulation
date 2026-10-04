"""Package upload-ready H.264/AAC video, captions, chapter metadata and review images."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"


def run(*args):
    subprocess.run(args, check=True)


def ass_time(t):
    cs = round(t * 100)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(cues):
    ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Korean,NanumGothic,40,&H00FFFFFF,&H00FFFFFF,&H00432D20,&H00432D20,0,0,0,0,100,100,0,0,3,12,0,2,100,100,78,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for c in cues:
        ass += f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Korean,,0,0,0,,{c['caption']}\n"
    (OUT / "subtitles.ko.ass").write_text(ass)


def main():
    cues = json.loads((OUT / "caption_timing.json").read_text())
    records = json.loads((ROOT / "assets/audio/manifest.json").read_text())
    doc = json.loads((ROOT / "storyboard.json").read_text())
    write_ass(cues)
    chapters = [r for r in records if r["line"] == 0]
    meta = ";FFMETADATA1\ntitle=QLoRA, 작게 저장하고 필요한 변화만 학습하기\nlanguage=kor\n"
    for i, rec in enumerate(chapters):
        end = chapters[i+1]["start"] if i+1 < len(chapters) else records[-1]["end"]
        meta += f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(rec['start']*1000)}\nEND={round(end*1000)}\ntitle={doc['chapters'][i]['title']}\n"
    (OUT / "chapters.ffmeta").write_text(meta)
    source = ROOT / "media_v2/videos/qlora_video_v2/1080p30/QLoRAEnhanced.mp4"
    common = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
              "-threads", "4", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart"]
    run("ffmpeg", "-hide_banner", "-y", "-i", str(source), "-i", str(OUT / "narration.wav"),
        "-i", str(OUT / "chapters.ffmeta"), "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2",
        "-map_chapters", "2", "-vf", f"ass={OUT / 'subtitles.ko.ass'}",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", *common,
        str(OUT / "qlora_education_ko_v2.mp4"))
    # A caption-free version allows YouTube viewers to toggle the uploaded SRT.
    run("ffmpeg", "-hide_banner", "-y", "-i", str(source), "-i", str(OUT / "narration.wav"),
        "-i", str(OUT / "chapters.ffmeta"), "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2", "-map_chapters", "2",
        "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", str(OUT / "qlora_clean_ko_v2.mp4"))
    text = "제목: QLoRA 완전 이해 | 4-bit 저장, 고정밀 계산, LoRA 학습\n\n"
    text += "QLoRA의 저장, 계산, 업데이트를 구분하는 약 5분 교육 영상입니다. LoRA 행렬 분해, 병렬 계산, 역전파, NF4, Double Quantization, Paged Optimizer와 메모리 계산을 애니메이션으로 설명합니다.\n\n"
    for rec, ch in zip(chapters, doc["chapters"]):
        seconds = int(round(rec["start"], 6))
        text += f"{seconds//60:02d}:{seconds%60:02d} {ch['title']}\n"
    text += "\n학습 곡선은 NumPy로 계산한 4×4 선형 회귀의 rank-2 어댑터 학습 예시이며, 대형 언어 모델 성능 측정이 아닙니다. 7B 모델의 14 GB / 3.5 GB 비교는 가중치 표현만 계산한 십진 용량이며, 전체 학습 VRAM을 뜻하지 않습니다.\n한국어 합성 내레이션, Whisper 음성 구간 분석 및 대본 기준 교정 자막을 사용했습니다.\n\n"
    text += "참고 자료\n" + "\n".join(doc["sources"]) + "\n\n#QLoRA #LoRA #양자화 #LLM #Manim\n"
    (OUT / "youtube_description.txt").write_text(text)
    script = doc["title"] + "\n\n학습 목표: " + doc["objective"] + "\n"
    for ci, ch in enumerate(doc["chapters"]):
        segment = [r for r in records if r["chapter"] == ci]
        script += f"\n{ci+1:02d}. {ch['title']} ({sum(r['duration'] for r in segment):.2f}초)\n"
        script += "화면: " + ch["visual"] + "\n\n"
        for r in segment:
            script += r["text"] + "\n자막: " + r["caption"] + "\n\n"
    (OUT / "narration.ko.txt").write_text(script)
    print("Upload package complete.")


if __name__ == "__main__":
    main()
