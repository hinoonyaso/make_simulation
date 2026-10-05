"""Derive every cut from the sole visual manifest; retain source/presentation time mapping."""
import argparse,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output'
def run(args):subprocess.run([str(a) for a in args],check=True)
def dur(p):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)]))
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def main(critical):
 doc=json.loads((H/'visual_manifest.json').read_text());bs=doc['beats'];records=json.loads((H/'assets/audio/manifest.json').read_text());by={r['beat']:r for r in records}
 ids=doc['critical_excerpt']['beat_ids'] if critical else [b['id'] for b in bs];bs=[b for b in bs if b['id'] in ids]
 width,height=(960,540) if critical else (1920,1080)
 suffix='critical' if critical else 'final';parts=O/f'{suffix}_parts';parts.mkdir(exist_ok=True)
 maps=[];manim_offset=0
 for b in bs:
  bid=b['id'];sec=b['sec'];part=parts/f'{bid}.mp4';vf='';base=[]
  if bid=='P01':
   if critical:
    src=H/'../../06_physics_probe/output/physics_probe_ko.mp4';trim='trim=start=4:end=8,setpts=PTS-STARTPTS';source_duration=4;source_t='0→8 seconds from probe, 2x source'
   else:
    src=O/'blender/physics_raw.mp4';trim='trim=start=8.033333333:end=16.066666667,setpts=PTS-STARTPTS';source_duration=241/30;source_t='0→8 seconds from baseline_blocked'
   hold=4.1;moving=sec-hold
   vf=f'{trim},setpts={moving/source_duration:.9f}*PTS,tpad=start_mode=clone:start_duration={hold:.9f},fps=30'
   maps.append(dict(beat=bid,source_time=source_t,presentation_hold_s=hold,presentation_motion_s=moving))
  elif bid in ['P02','P03']:
   src=O/f'{"critical_render" if critical else "final_render"}/videos/physics_reasoning/{"540p30" if critical else "1080p30"}/PhysicalReasoning.mp4'
   start=0 if bid=='P02' else by['P02']['duration'];vf=f'trim=start={start:.9f}:duration={sec:.9f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.3,fps=30'
  elif bid=='P04':
   src=O/'blender/physics_raw.mp4';vf=f'tpad=stop_mode=clone:stop_duration={max(0,sec-482/30):.9f},fps=30'
   maps.append(dict(beat=bid,source_time='clear 0→8, then blocked 0→8 seconds',presentation_duration_s=sec))
  else:
   src=H/b['source_media'];vf=f'trim=start={b["source_media_in"]:.9f}:end={b["source_media_out"]:.9f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.3,fps=30'
  vf+=f',scale={width}:{height}'
  if bid.startswith('B'):
   vf+=",drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='교육용 지도 모형 · 물리 실험과 별도':x=35:y=35:fontsize=24:fontcolor=0x9CA9BE"
  if not critical and bid in ['P01','P04']:
   top='바퀴 명령만으로 알아서 피할까?' if bid=='P01' else '물리 실험 · 회피 계획기 없음'
   vf+=f",drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='{top}':x=80:y=65:fontsize=42:fontcolor=0x20242a"
   if bid=='P04':
    vf+=",drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='장애물 없음':x=80:y=130:fontsize=30:fontcolor=0x20242a:enable='lt(t,8.033333)',drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='드럼 있음':x=80:y=130:fontsize=30:fontcolor=0x20242a:enable='gte(t,8.033333)'"
  run(['ffmpeg','-v','error','-y','-i',src,'-vf',vf,'-an','-t',f'{sec:.9f}','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',part])
 concat=parts/'concat.txt';concat.write_text(''.join(f"file '{(parts/(b['id']+'.mp4')).as_posix()}'\n" for b in bs))
 picture=parts/'picture.mp4';run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy',picture])
 start=by[bs[0]['id']]['start'];end=by[bs[-1]['id']]['end'];sec=end-start
 wav=O/'narration.wav';cues=json.loads((O/'caption_timing.json').read_text())
 if critical:
  wav=O/'critical_narration.wav';run(['ffmpeg','-v','error','-y','-i',O/'narration.wav','-af',f'atrim=start={start:.9f}:end={end:.9f},asetpts=PTS-STARTPTS',wav]);cues=[{**c,'start':c['start']-start,'end':c['end']-start} for c in cues if c['start']>=start and c['end']<=end]
 srt=O/f'{suffix}.ko.srt';srt.write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["caption"]}' for i,c in enumerate(cues))+'\n')
 final=O/('critical_excerpt.mp4' if critical else 'moving_obstacle_physics_ko_v5.mp4')
 # Burned sentence captions remain visible in ordinary players; retain the selectable SRT as a sidecar to avoid duplicate player captions.
 style=f'FontName=NanumGothic,FontSize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&H00202020,BorderStyle=1,Outline=1.5,Shadow=0,MarginV=24'
 run(['ffmpeg','-v','error','-y','-i',picture,'-i',wav,'-filter_complex',f"[0:v]tpad=stop_mode=clone:stop_duration=0.3,subtitles='{srt.as_posix()}':force_style='{style}'[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]",'-map','[v]','-map','[a]','-t',f'{sec:.9f}','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',final])
 (O/f'{suffix}_assembly.json').write_text(json.dumps(dict(beat_ids=ids,duration_s=sec,source_mapping=maps,picture_duration_s=dur(picture)),indent=2)+'\n')
 print('FINAL',final,sec,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--critical',action='store_true');main(ap.parse_args().critical)
