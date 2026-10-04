import json,subprocess,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;O=R/'output';A=json.loads((R/'assets/audio/manifest.json').read_text());S=json.loads((R/'storyboard.json').read_text());D=json.loads((O/'trace.json').read_text());FONT='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
def run(args):subprocess.run(args,check=True)
chapters=[dict(seconds=next(a['start'] for a in A if a['chapter']==i),title=c['title']) for i,c in enumerate(S['chapters'])];ends=[next(a['end'] for a in reversed(A) if a['chapter']==i) for i in range(10)];total=A[-1]['end'];timelines={}
for mode,ci in [('baseline',6),('dynamic',7)]:
 mapping=json.loads((O/f'blender/{mode}_frames.json').read_text());length=ends[ci]-chapters[ci]['seconds'];lead=1 if mode=='baseline' else next(a['duration'] for a in A if a['chapter']==ci and a['line']==0)
 tail=2 if mode=='baseline' else next(a['duration'] for a in A if a['chapter']==ci and a['line']==3);pause=0 if mode=='baseline' else 2.;move=length-lead-tail-pause;folder=O/f'{mode}_annotated';folder.mkdir(exist_ok=True);concat=[];timeline=[];cursor=0
 for i,frame in enumerate(mapping):
  row=D[mode]['rows'][frame['sample']];im=Image.open(O/f'blender/{mode}/{i:04d}.png').convert('RGB');draw=ImageDraw.Draw(im);draw.rectangle((0,592,1080,648),fill='#F7F9FC');font=ImageFont.truetype(FONT,23)
  v,w=row['cmd'];label=f'{mode.upper()}   t = {frame["time"]:.1f} s   v = {v:.2f} m/s   ω = {w:.2f} rad/s';draw.text((20,608),label,font=font,fill='#26364A')
  if row['state']=='REPLAN':draw.rounded_rectangle((295,20,810,70),radius=8,fill='#FFF4D6');draw.text((310,28),'PATH INVALID  →  STOP / REPLAN',font=font,fill='#975E17')
  path=folder/f'{i:04d}.png';im.save(path);duration=move/len(mapping)
  if i==0:duration+=lead
  if i==len(mapping)-1:duration+=tail
  if mode=='dynamic' and i==30:duration+=pause
  concat.append(f"file '{path.as_posix()}'\nduration {duration:.9f}\n");timeline.append(dict(video_start=chapters[ci]['seconds']+cursor,source_frame=i+1,sample=frame['sample'],simulation_time=frame['time'],duration=duration));cursor+=duration
 concat.append(f"file '{path.as_posix()}'\n");listing=O/f'{mode}_concat.txt';listing.write_text(''.join(concat));timelines[mode]=timeline
 run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-vf','fps=30','-t',str(length),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(O/f'{mode}_spatial.mp4')])
meta=';FFMETADATA1\n'
for ch,end in zip(chapters,ends):meta+=f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(ch["seconds"]*1000)}\nEND={round(end*1000)}\ntitle={ch["title"]}\n'
(O/'chapters.ffmeta').write_text(meta)
filt=(f'[1:v]scale=1000:600,setpts=PTS+{chapters[6]["seconds"]}/TB[b];[0:v][b]overlay=140:280:enable=\'between(t,{chapters[6]["seconds"]},{ends[6]-.01})\'[v1];'+f'[2:v]scale=1000:600,setpts=PTS+{chapters[7]["seconds"]}/TB[d];[v1][d]overlay=140:280:enable=\'between(t,{chapters[7]["seconds"]},{ends[7]-.01})\'[v]')
run(['ffmpeg','-v','error','-y','-i',str(O/'manim/videos/lesson/1080p30/Nav2Lesson.mp4'),'-i',str(O/'baseline_spatial.mp4'),'-i',str(O/'dynamic_spatial.mp4'),'-i',str(O/'narration.wav'),'-f','ffmetadata','-i',str(O/'chapters.ffmeta'),'-filter_complex',filt,'-map','[v]','-map','3:a','-map_metadata','4','-map_chapters','4','-t',str(total),'-r','30','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-movflags','+faststart',str(O/'nav2_education_ko.mp4')])
im=Image.new('RGB',(1280,720),'#F7F9FC');draw=ImageDraw.Draw(im)
def text(x,y,t,size,color='#26364A'):draw.text((x,y),t,font=ImageFont.truetype(FONT,size),fill=color)
text(55,40,'ROS 2',45,'#738195');text(50,110,'Nav2',130,'#147DAD');text(55,290,'목적지까지',65);text(55,385,'어떻게 갈까?',65);text(55,585,'위치 → 경로 → 속도 → 이동',30,'#198868')
draw.rounded_rectangle((685,110,1230,535),radius=20,fill='#E8EEF4',outline='#9AABBB',width=4)
for x0,y0,x1,y1 in D['boxes']:draw.rectangle((950+x0*48,320-y1*48,950+x1*48,320-y0*48),fill='#586B80')
pts=[(950+r['pose'][0]*48,320-r['pose'][1]*48) for r in D['dynamic']['rows']];draw.line(pts,fill='#198868',width=9);draw.ellipse((933,303,967,337),fill='#B75057');draw.ellipse((789,305,819,335),fill='#147DAD');text(782,345,'AMR',22,'#147DAD');text(1070,275,'GOAL',24,'#198868');text(780,590,'SENSE  →  PLAN  →  ACT',27,'#147DAD');im.save(O/'thumbnail.png')
desc='SLAM·AMCL·A* 다음 종합편입니다. 목표 입력부터 위치 추정, 글로벌/로컬 코스트맵, 경로 계획, 속도 제어, 바퀴 구동, 재계획과 Behavior Tree의 역할까지 Nav2의 데이터 흐름을 설명합니다.\n\n'
for ch in chapters:
 t=int(ch['seconds']);desc+=f'{t//60:02d}:{t%60:02d} {ch["title"]}\n'
desc+='\n직접 구현한 교육용 통합 모형이며 실제 ROS 2/Nav2 실행이나 성능 재현이 아닙니다. 위치 입력은 오차 없는 Pose로 대체하며 AMCL은 구조 설명만 합니다. 모의 LiDAR(120방향, 최대 3.2m, 거리 잡음 표준편차 2mm)가 새 장애물 관측을 만들고, 정적 지도와 다른 점의 원 적합으로 장애물 중심을 추정합니다. 장애물 실제 위치는 센서 생성과 평가에만 사용합니다.\n\n0.15m 격자의 8방향 비용 가중 A*, 1.5초 후보 궤적 평가, 차동 구동 운동학을 구현했습니다. 센서·제어는 10Hz, 계획은 1초 주기 또는 경로 무효 때 갱신합니다. 로컬 판단은 같은 장애물 추정의 연속 거리장을 사용하며 별도 Nav2 rolling-grid 구현은 아닙니다. 원형 로봇 반지름 0.25m, 바퀴 반지름 0.10m, 바퀴 간격 0.45m입니다. 접촉 동역학·미끄러짐·TF·통신 지연·실제 모터 제어는 생략했습니다. 경로 무효 시 정지는 이상적 명령 전환입니다.\n\n장애물 없음: 14.0초 / 새 장애물 있음: 17.2초. 두 경우 모두 위치 0.12m 이내·방향 0.08rad 이내 목표 조건을 만족했습니다. 새 장애물 조건의 로봇 외곽 최소 간격은 약 0.40m, 경로 무효에 따른 재계획은 1회입니다. 단일 합성 실험(seed 14) 결과이며 일반적인 로봇 성능 수치가 아닙니다. 블렌더 장면은 동일 기록의 느린 재생이며 재계획 순간을 설명용으로 잠시 정지합니다.\n\nBehavior Tree 그림은 역할을 줄인 개념도입니다. 실험의 조율기는 단순 상태 기계이며 BehaviorTree.CPP 실행이 아닙니다. 실제 Nav2에서는 트리·플러그인·레이어 설정에 따라 재계획, 복구, 센서 반영 방식이 달라집니다. Inflation 영역 전체가 통행 금지는 아니며, 위치 추정과 코스트맵은 지속적으로 갱신됩니다.\n\n앞선 영상\nSLAM https://www.youtube.com/watch?v=VGIooUDrPbM\nAMCL https://www.youtube.com/watch?v=ZrRFR6ma-QY\nA* https://www.youtube.com/watch?v=j5MNfkM39cc\n\n공식 참고 자료\nhttps://docs.nav2.org/rolling/getting_started/nav2_behavior_trees/\nhttps://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_2d/costmap_plugins/inflation/\nhttps://docs.nav2.org/rolling/configuration_and_development/tuning_guide/\n\n한국어 합성 내레이션, Whisper 자막 정렬, Manim·Blender 원본 애니메이션을 사용했습니다.\n#Nav2 #ROS2 #로봇 #AMR #자율주행 #BehaviorTree\n'
package=dict(video='../output/nav2_education_ko.mp4',title='ROS2 Nav2는 로봇을 목적지까지 어떻게 보내는가? | SLAM·AMCL·A* 종합편',description=desc,privacy='public',channel_id='UCKT_GQPU4i_wmtE-b_6wa8A',captions='../output/subtitles.ko.srt',caption_language='ko',thumbnail='../output/thumbnail.png',made_for_kids=False,contains_synthetic_media=False,tags=['Nav2','ROS2','로봇','AMR','SLAM','AMCL','AStar','Behavior Tree','Manim','Blender'],chapters=chapters)
(R/'publish/package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2));(O/'youtube_description.txt').write_text(desc);(O/'timeline.json').write_text(json.dumps(dict(chapters=chapters,ends=ends,duration=total,blender=timelines),ensure_ascii=False,indent=2));print('Finished',total,'description bytes',len(desc.encode()))
