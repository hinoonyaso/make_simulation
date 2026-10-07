"""Local sentence-boundary trim of approved speech; never sends text externally."""
import json,subprocess,shutil
from pathlib import Path
H=Path(__file__).resolve().parent;A=H/'assets/audio';O=H/'output'
def run(args):subprocess.run([str(x) for x in args],check=True)
audio=json.loads((A/'manifest.json').read_text());doc=json.loads((H/'visual_manifest.json').read_text())
changes={'B03':(8.2,8.233333333333333,'이전의 직진 경로가 금지 영역과 겹칩니다. 계획기는 현재 위치에서 위쪽을 돌아가는 새 길을 고릅니다.'),'B04E':(1.9,3.4,'이 숫자는 명령입니다.')}
for r in audio:
 id=r['beat']
 if id in changes:
  stop,duration,text=changes[id];original=A/f'{id}.approved_original.wav'
  if not original.exists():shutil.copy2(H/r['audio'],original)
  run(['ffmpeg','-v','error','-y','-i',original,'-af',f'atrim=end={stop},asetpts=PTS-STARTPTS,apad','-t',f'{duration:.9f}','-ar','48000','-ac','1',H/r['audio']])
  r.update(text=text,caption=text,duration=duration,local_edit={'original':str(original.relative_to(H)),'trim_end_s':stop,'final_duration_s':duration,'basis':'Whisper word end before next sentence start; tail for reading'})
now=0
for r in audio:r.update(start=now,end=now+r['duration']);now=r['end']
by={r['beat']:r for r in audio}
for b in doc['beats']:
 r=by[b['id']];b.update(text=r['text'],caption=r['caption'],sec=r['duration'],audio=r['audio'])
(A/'manifest.json').write_text(json.dumps(audio,ensure_ascii=False,indent=2)+'\n');(H/'visual_manifest.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
listing=A/'concat.txt';listing.write_text(''.join(f"file '{H/r['audio']}'\n" for r in audio));run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',listing,'-c:a','pcm_s16le',O/'narration.wav'])
print(f'Locally trimmed measured duration: {now:.2f}s')
