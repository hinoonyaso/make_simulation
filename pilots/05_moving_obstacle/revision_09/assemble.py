"""Manifest-driven finishing; source solver times remain separate from edit times."""
import argparse,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output'
def run(a):subprocess.run([str(x) for x in a],check=True)
def stamp(t):
 m=round(t*1000);return f'{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02},{m%1000:03}'
def main(critical=False):
 doc=json.loads((H/'visual_manifest.json').read_text());audio=json.loads((H/'assets/audio/manifest.json').read_text());by={r['beat']:r for r in audio}
 ids=doc['critical_excerpt']['beat_ids'] if critical else [b['id'] for b in doc['beats']];bs=[b for b in doc['beats'] if b['id'] in ids]
 name='critical' if critical else 'final';parts=O/f'{name}_parts';parts.mkdir(exist_ok=True);w,h=(960,540) if critical else (1920,1080)
 if critical:
  run(['ffmpeg','-v','error','-y','-framerate','30','-start_number',str(round(by['B01']['duration']*30)+1),'-i',O/'blender/frames/frame_%04d.png','-frames:v',str(round(by['B05']['duration']*30)),'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',O/'blender/critical_raw.mp4'])
 if not critical:
  run(['ffmpeg','-v','error','-y','-framerate','30','-start_number','1','-i',O/'blender/frames/frame_%04d.png','-frames:v',str(sum(round(by[bid]['duration']*30) for bid in ['B01','B05'])),'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',O/'blender/physics_raw.mp4'])
 for b in bs:
  bid=b['id'];sec=b['sec'];part=parts/f'{bid}.mp4';label=None
  if bid in ['B02','B03','B04']:
   src=O/f'{"critical_render" if critical else "final_render"}/videos/reasoning_scene/{"540p30" if critical else "1080p30"}/ClosedLoopReasoning.mp4';start=by[bid]['start']-by['B02']['start']
  elif bid in ['B01','B05']:
   src=O/('blender/critical_raw.mp4' if critical else 'blender/physics_raw.mp4');start=0 if critical or bid=='B01' else by['B01']['duration'];label='계획기 없음 · 고정 바퀴 명령' if bid=='B01' else '같은 실행 다시 보기 · 실험 2→30초'
  else:
   clips=[]
   for condition,duration in [('off',1.5),('on',sec-1.5)]:
    dst=parts/f'B06_{condition}.mp4';title='계획기 없음 · 드럼 앞 접촉' if condition=='off' else '계획·제어 연결 · 목표 범위에서 정지'
    vf=f"drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='{title}':x=70:y=55:fontsize=38:fontcolor=0x20242a"
    run(['ffmpeg','-v','error','-y','-loop','1','-framerate','30','-i',O/f'blender/final_{condition}.png','-vf',vf,'-t',duration,'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',dst]);clips.append(dst)
   listing=parts/'comparison.txt';listing.write_text(''.join(f"file '{p}'\n" for p in clips));run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',listing,'-c','copy',part]);continue
  vf=f'trim=start={start}:duration={sec},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.2,fps=30,scale={w}:{h}'
  if label:
   enable=":enable='lt(t,3)'" if bid=='B05' else ''
   vf+=f",drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='{label}':x={round(70*w/1920)}:y={round(205*h/1080)}:fontsize={round(38*w/1920)}:fontcolor=0x20242a{enable}"
  if bid=='B05':vf+=f",drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='초록 참고 경로 · 파랑 실제 궤적':x={round(70*w/1920)}:y={round(258*h/1080)}:fontsize={round(30*w/1920)}:fontcolor=0x20242a:enable='lt(t,3)'"
  run(['ffmpeg','-v','error','-y','-i',src,'-vf',vf,'-an','-t',sec,'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',part])
 listing=parts/'concat.txt';listing.write_text(''.join(f"file '{parts/(b['id']+'.mp4')}'\n" for b in bs));picture=parts/'picture.mp4';run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',listing,'-c','copy',picture])
 start,end=by[bs[0]['id']]['start'],by[bs[-1]['id']]['end'];cues=json.loads((O/'caption_timing.json').read_text());wav=O/'narration.wav'
 if critical:
  wav=O/'critical_narration.wav';run(['ffmpeg','-v','error','-y','-i',O/'narration.wav','-af',f'atrim=start={start}:end={end},asetpts=PTS-STARTPTS',wav]);cues=[{**c,'start':c['start']-start,'end':c['end']-start} for c in cues if c['start']>=start and c['end']<=end]
  (O/'critical_caption_timing.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2)+'\n');(O/'critical_audio_manifest.json').write_text(json.dumps([{**r,'start':r['start']-start,'end':r['end']-start} for r in audio if r['beat'] in ids],ensure_ascii=False,indent=2)+'\n')
 srt=O/f'{name}.ko.srt';srt.write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["caption"]}' for i,c in enumerate(cues))+'\n')
 final=O/('critical_excerpt.mp4' if critical else 'planner_physics_ko_v9.mp4');style='FontName=NanumGothic,FontSize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&H00202020,BorderStyle=1,Outline=0.7,Shadow=0,MarginV=24'
 run(['ffmpeg','-v','error','-y','-i',picture,'-i',wav,'-filter_complex',f"[0:v]tpad=stop_mode=clone:stop_duration=0.2,subtitles='{srt}':force_style='{style}'[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]",'-map','[v]','-map','[a]','-t',end-start,'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',final])
 (O/f'{name}_assembly.json').write_text(json.dumps({'beat_ids':ids,'duration_s':end-start,'subtitle_mode':'burned + external sidecar, no internal subtitle stream'},indent=2)+'\n')
 if not critical:
  for b in doc['beats']:b.update(media='output/planner_physics_ko_v9.mp4',media_in=by[b['id']]['start'],media_out=by[b['id']]['end'])
  (H/'visual_manifest.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
 print(final,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--critical',action='store_true');main(ap.parse_args().critical)
