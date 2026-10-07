"""Assemble the single measured manifest; reuse recorded physics media read-only."""
import argparse,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output'
def run(args):subprocess.run([str(x) for x in args],check=True)
def stamp(t):
 m=round(t*1000);return f'{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02},{m%1000:03}'
def main(critical=False):
 doc=json.loads((H/'visual_manifest.json').read_text());audio=json.loads((H/'assets/audio/manifest.json').read_text());by={r['beat']:r for r in audio}
 ids=doc['critical_excerpt']['beat_ids'] if critical else [b['id'] for b in doc['beats']];beats=[b for b in doc['beats'] if b['id'] in ids]
 name='critical' if critical else 'final';parts=O/f'{name}_parts';parts.mkdir(exist_ok=True);w,h=(960,540) if critical else (1920,1080)
 font='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
 mapping=[]
 for b in beats:
  bid=b['id'];sec=b['sec'];part=parts/f'{bid}.mp4';inputs=[]
  if bid in ['B06','B08','B10','B18']:
   kind={'B06':'equal','B08':'left','B10':'spin','B18':'stop'}[bid]
   inputs=['-i',O/f'cases/{kind}/raw.mp4'];vf=f'setpts=(PTS-STARTPTS)*{sec/6.0333333333},tpad=stop_mode=clone:stop_duration=0.2,fps=30,scale={w}:{h}'
   label={'equal':'좌우 목표 0.20 / 0.20 m/s','left':'좌우 목표 0.05 / 0.25 m/s','spin':'좌우 목표 -0.15 / +0.15 m/s','stop':'실험 3초: 좌우 목표 0으로 변경'}[kind]
   for n,t,y in [('goal',label,140),('clock','실험 0→6초 · 느리게 재생',195),('cutaway','몸체 숨김 · 차축/방향선은 설명용 표시',250)]:
    f=parts/f'{bid}_{n}.txt';f.write_text(t)
    enable=f":enable='between(t,{sec*39/181},{sec*145/181})'" if n=='cutaway' else ''
    vf+=f',drawtext=fontfile={font}:textfile={f}:x={round(70*w/1920)}:y={round(y*h/1080)}:fontsize={round((30 if n=="cutaway" else 34)*w/1920)}:fontcolor=0x20242a'+enable
   mapping.append({'beat':bid,'solver_source_s':[0,6],'presentation_s':sec,'source':f'data/baseline_{kind}.json','mode':'read-only R14 Bullet solver replay; new R16 rendering; slower presentation'})
  elif b['tool']=='M':
   changed=['B22','B05','B07','B09','B11','B12','B13','B14','B15','B16','B17','B19']
   if bid in changed:
    final_src=O/f'final_render/videos/reasoning_scene/1080p30/Patch{bid}.mp4'
    src=final_src if final_src.exists() else O/f'preview_render/videos/reasoning_scene/540p30/Patch{bid}.mp4'
    if not critical:assert src==final_src
   else:src=H.parent/'revision_15/output/final_parts'/f'{bid}.mp4'
   inputs=['-i',src];vf=f'trim=start=0:duration={sec},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.2,fps=30,scale={w}:{h}'
   mapping.append({'beat':bid,'source':str(src.relative_to(H.parent)),'mode':'new local skill repair' if bid in changed else 'read-only R14 picture part; identical narration/timing'})
  elif bid in ['B01','B20']:
   start,source_duration,solver=(0,9.2666666667,[0,8]) if bid=='B01' else (9.2666666667,14.8,[2,30])
   inputs=['-i',H.parent/'revision_12/output/blender/physics_raw.mp4'];vf=f'trim=start={start}:duration={source_duration},setpts=(PTS-STARTPTS)*{sec/source_duration},tpad=stop_mode=clone:stop_duration=0.2,fps=30,scale={w}:{h}'
   label='계획·제어 없음 · 고정 바퀴 명령' if bid=='B01' else 'R06 회피 실행 · 실험 2→30초'
   f=parts/f'{bid}_label.txt';f.write_text(label)
   vf+=f',drawtext=fontfile={font}:textfile={f}:x={round(70*w/1920)}:y={round(205*h/1080)}:fontsize={round(34*w/1920)}:fontcolor=0x20242a'
   if bid=='B20':
    legend=parts/'B20_roles.txt';legend.write_text('초록 참고 경로 · 파랑 실제 궤적')
    vf+=f",drawtext=fontfile={font}:textfile={legend}:x={round(70*w/1920)}:y={round(258*h/1080)}:fontsize={round(28*w/1920)}:fontcolor=0x20242a:enable='lt(t,3)'"
   mapping.append({'beat':bid,'solver_source_s':solver,'presentation_s':sec,'origin':'R12 encoded R10 recorded physics frames; complete interval retimed'})
  else:
   inputs=['-loop','1','-framerate','30','-i',H.parent/'revision_12/output/blender/final_on.png'];vf=f'scale={w}:{h},fps=30'
  run(['ffmpeg','-v','error','-y',*inputs,'-vf',vf,'-an','-t',sec,'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',part])
 listing=parts/'concat.txt';listing.write_text(''.join(f"file '{parts/(b['id']+'.mp4')}'\n" for b in beats));picture=parts/'picture.mp4';run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',listing,'-c','copy',picture])
 start,end=by[beats[0]['id']]['start'],by[beats[-1]['id']]['end'];cues=json.loads((O/'caption_timing.json').read_text());wav=O/'narration.wav'
 if critical:
  wav=O/'critical_narration.wav';run(['ffmpeg','-v','error','-y','-i',O/'narration.wav','-af',f'atrim=start={start}:end={end},asetpts=PTS-STARTPTS',wav]);cues=[{**c,'start':c['start']-start,'end':c['end']-start} for c in cues if c['start']>=start and c['end']<=end]
  (O/'critical_caption_timing.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2)+'\n');(O/'critical_audio_manifest.json').write_text(json.dumps([{**r,'start':r['start']-start,'end':r['end']-start} for r in audio if r['beat'] in ids],ensure_ascii=False,indent=2)+'\n')
 srt=O/f'{name}.ko.srt';srt.write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["caption"]}' for i,c in enumerate(cues))+'\n')
 final=O/('critical_excerpt.mp4' if critical else 'planner_control_long_ko_v16.mp4');style='FontName=NanumGothic,FontSize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&H00202020,BorderStyle=1,Outline=0.7,Shadow=0,MarginV=24'
 run(['ffmpeg','-v','error','-y','-i',picture,'-i',wav,'-filter_complex',f"[0:v]tpad=stop_mode=clone:stop_duration=0.2,subtitles='{srt}':force_style='{style}'[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]",'-map','[v]','-map','[a]','-t',end-start,'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',final])
 (O/f'{name}_assembly.json').write_text(json.dumps({'beat_ids':ids,'duration_s':end-start,'source_mapping':mapping},indent=2)+'\n')
 if not critical:
  for b in doc['beats']:b.update(media='output/planner_control_long_ko_v16.mp4',media_in=by[b['id']]['start'],media_out=by[b['id']]['end'])
  (H/'visual_manifest.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
 print(final,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--critical',action='store_true');main(ap.parse_args().critical)
