import json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;O=R/'output';A=json.loads((R/'assets/audio/manifest.json').read_text());S=json.loads((R/'storyboard.json').read_text());D=json.loads((O/'trace.json').read_text());FONT='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
def run(args):subprocess.run(args,check=True)
chapters=[dict(seconds=next(a['start'] for a in A if a['chapter']==i),title=c['title']) for i,c in enumerate(S['chapters'])];ends=[next(a['end'] for a in reversed(A) if a['chapter']==i) for i in range(8)];total=A[-1]['end'];compare_start=next(a['start'] for a in A if a['chapter']==7 and a['line']==2);timeline={}
for method in ['dwb','teb']:
 mapping=json.loads((O/f'blender/{method}_frames.json').read_text());folder=O/f'{method}_annotated';folder.mkdir(exist_ok=True)
 for i,frame in enumerate(mapping):
  row=D['runs'][method+'_obstacle']['rows'][frame['sample']];im=Image.open(O/f'blender/{method}/{i:04d}.png').convert('RGB');draw=ImageDraw.Draw(im);draw.rectangle((0,538,1080,600),fill='#F7F9FC');font=ImageFont.truetype(FONT,22);v,w=row['cmd'];done=frame['simulation_time']>=D['runs'][method+'_obstacle']['metrics']['duration_s']-1e-6;label=f'{method.upper()} toy   t={frame["simulation_time"]:.1f}s   '+('GOAL reached' if done else f'v={v:.2f} m/s   ω={w:.2f} rad/s');draw.text((20,542),label,font=font,fill='#26364A');draw.text((20,573),'파랑: 실행 기록 / '+('초록: 선택한 예측' if method=='dwb' else '보라: 최적화 예측')+' / 회색: Global Path',font=ImageFont.truetype(FONT,20),fill='#586B80');im.save(folder/f'{i:04d}.png')
 run(['ffmpeg','-v','error','-y','-framerate','15','-i',str(folder/'%04d.png'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(O/f'{method}_spatial.mp4')])
 timeline[method]=mapping
firstlen=ends[3]-chapters[3]['seconds'];comparelen=ends[7]-compare_start
filters=(f'[1:v]split=2[d1][d2];[d1]setpts={firstlen/14.2}*PTS+{chapters[3]["seconds"]}/TB,scale=1050:583,tpad=stop_mode=clone:stop_duration=2[dwb];'
 f'[0:v][dwb]overlay=140:300:enable=\'between(t,{chapters[3]["seconds"]},{ends[3]-.01})\'[v1];'
 f'[d2]setpts={comparelen/14.2}*PTS+{compare_start}/TB,scale=840:467,tpad=stop_mode=clone:stop_duration=2[left];'
 f'[2:v]setpts={comparelen/14.2}*PTS+{compare_start}/TB,scale=840:467,tpad=stop_mode=clone:stop_duration=2[right];'
 f'[v1][left]overlay=80:440:enable=\'between(t,{compare_start},{ends[7]})\'[v2];'
 f'[v2][right]overlay=1000:440:enable=\'between(t,{compare_start},{ends[7]})\'[v]')
meta=';FFMETADATA1\n'
for ch,end in zip(chapters,ends):meta+=f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(ch["seconds"]*1000)}\nEND={round(end*1000)}\ntitle={ch["title"]}\n'
(O/'chapters.ffmeta').write_text(meta)
run(['ffmpeg','-v','error','-y','-i',str(O/'manim/videos/lesson/1080p30/ControllerComparison.mp4'),'-i',str(O/'dwb_spatial.mp4'),'-i',str(O/'teb_spatial.mp4'),'-i',str(O/'narration.wav'),'-f','ffmetadata','-i',str(O/'chapters.ffmeta'),'-filter_complex',filters,'-map','[v]','-map','3:a','-map_metadata','4','-map_chapters','4','-t',str(total),'-r','30','-c:v','libx264','-threads','4','-preset','fast','-crf','18','-pix_fmt','yuv420p','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-movflags','+faststart',str(O/'dwb_teb_education_ko.mp4')])
im=Image.new('RGB',(1280,720),'#F7F9FC');draw=ImageDraw.Draw(im)
def text(x,y,t,size,color='#26364A'):draw.text((x,y),t,font=ImageFont.truetype(FONT,size),fill=color)
text(60,35,'DWB',92,'#147DAD');text(525,55,'vs',65,'#738195');text(835,35,'TEB',92,'#8A66B2');text(155,165,'속도 후보',40);text(785,165,'시간 포함 궤적',40)
for x in [45,665]:draw.rounded_rectangle((x,240,x+570,530),radius=20,fill='#E8EEF4')
def point(p,offset):return(offset+(p[0]+1.4)*145,430-p[1]*170)
for c in D['hero']['dwb']['detail']['candidates'][::5]:draw.line([point(p,90) for p in c['trajectory']],fill='#AFBCCB',width=3)
best=D['hero']['dwb']['detail']['candidates'][D['hero']['dwb']['detail']['selected']];draw.line([point(p,90) for p in best['trajectory']],fill='#198868',width=8)
poses=D['hero']['teb']['detail']['poses'];draw.line([point(p,710) for p in poses],fill='#8A66B2',width=7)
for p in poses:
 x,y=point(p,710);draw.ellipse((x-6,y-6,x+6,y+6),fill='#8A66B2')
for off in [90,710]:
 x,y=point(D['obstacle'],off);draw.ellipse((x-34,y-34,x+34,y+34),fill='#B75057')
text(130,585,'로봇 제어, 무엇이 다를까?',65);im.save(O/'thumbnail.png')
desc='Nav2 다음 편. DWB의 지역 속도 탐색과 TEB의 시간 포함 궤적 최적화를 같은 복도·글로벌 경로에서 비교합니다. 어느 쪽이 무조건 우수하다는 성능 순위가 아니라 계산 원리를 설명합니다.\n\n'
for ch in chapters:
 t=int(ch['seconds']);desc+=f'{t//60:02d}:{t%60:02d} {ch["title"]}\n'
desc+='\nROS 2 TEB 확인(2026-09-22): 원 저장소 rst-tu-dortmund/teb_local_planner의 ros2-master, humble-devel 브랜치와 nav2_core::Controller 플러그인 선언을 확인했습니다. ros2-master 확인 커밋 e4562a6(2024-11-10), humble-devel 630a22e(2022-09-12)입니다. README에는 Dashing와 이전 Nav2 커밋 설명이 남아 있습니다. 브랜치 존재가 최신 배포판 빌드·동작 지원을 보장하지 않으며, 이 제작에서는 실제 패키지 빌드를 검증하지 않았습니다. TEB를 Nav2의 기본 내장 컨트롤러로 소개하지 않습니다.\n\n교육용으로 직접 구현한 두 모형입니다. Nav2 DWB/ROS 2 TEB 플러그인 실행·벤치마크·재현이 아닙니다. 둘 다 이상적 Pose와 동일한 완전한 정적 장애물 지도를 입력받습니다. LiDAR/AMCL/통신 지연을 모사하지 않았습니다. 글로벌 경로는 고정된 직선이며, 장애물이 있는 조건에서도 동일하게 유지해 로컬 반응을 보여줍니다.\n\nDWB형 모형: (v,ω) 후보를 2초 rollout하고 경로·목표·장애물·속도·회전 비용을 합칩니다. 유효하지 않은 후보는 제외하고 최소 비용 명령을 0.2초 실행합니다. 실제 DWB의 generator/critic 구현식과 다릅니다.\nTEB형 모형: 12개 Pose와 11개 양의 ΔT, 최대 2.4m 전방 구간을 SciPy least_squares로 최적화합니다. 시간·거리 여유·운동학·속도 한계·경로 참조·평활 비용을 사용하고 첫 구간에서 cmd_vel을 계산합니다. 고정 노드 수, 단일 초기 밴드이며 g2o, 자동 크기 조절, 여러 위상 경로 탐색, 실제 TEB 가속도 제약은 재현하지 않았습니다. 운동학 제약은 페널티여서 잔차가 남습니다.\n\n동일 차동 구동 운동학, v≤0.6m/s, |ω|≤1.4rad/s, 반지름 0.22m, 복도 폭 2.5m. 장애물은 (0,-0.18)m의 반지름 0.30m 원입니다. 가중치·예측 범위·가속도 처리 등이 달라 실제 패키지 간 공정 성능 비교가 아닙니다. 모형별 빈 복도/장애물 조건 각 1회, 총 4회 모두 위치 0.10m·방향 0.08rad 도착 조건을 만족했습니다. 100Hz 간격 검사에서 접촉은 없었으며 연속시간 안전 증명은 아닙니다. Blender는 계산 기록의 느린 재생이며 최적화 궤적·선택한 예측·실행 기록을 구분합니다.\n\n이전 Nav2 종합편\nhttps://www.youtube.com/watch?v=VL8sFwjCCfU\n\n출처\nhttps://docs.nav2.org/rolling/configuration_and_development/configuration_guide/controller_plugins/dwb_controller/\nhttps://github.com/ros-navigation/navigation2/tree/main/nav2_dwb_controller\nhttps://github.com/rst-tu-dortmund/teb_local_planner/tree/ros2-master\nhttps://github.com/rst-tu-dortmund/teb_local_planner/tree/humble-devel\n\n한국어 합성 내레이션·Whisper 자막 정렬·Manim/Blender 원본 애니메이션.\n#DWB #TEB #Nav2 #ROS2 #로봇 #자율주행\n'
package=dict(video='../output/dwb_teb_education_ko.mp4',title='DWB와 TEB는 로봇 경로를 어떻게 다르게 제어할까?',description=desc,privacy='public',channel_id='UCKT_GQPU4i_wmtE-b_6wa8A',captions='../output/subtitles.ko.srt',caption_language='ko',thumbnail='../output/thumbnail.png',made_for_kids=False,contains_synthetic_media=False,tags=['DWB','TEB','Nav2','ROS2','로봇','AMR','Trajectory Optimization','Manim','Blender'],chapters=chapters)
(R/'publish/package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2));(O/'youtube_description.txt').write_text(desc);(O/'timeline.json').write_text(json.dumps(dict(chapters=chapters,ends=ends,duration=total,spatial_frames=timeline,dwb_execution=dict(start=chapters[3]['seconds'],end=ends[3],source_duration=14.2),comparison=dict(start=compare_start,end=ends[7],source_duration=14.2,teb_final_hold_after_sim_s=D['runs']['teb_obstacle']['metrics']['duration_s'])),ensure_ascii=False,indent=2));print('Finished',total,'description bytes',len(desc.encode()))
