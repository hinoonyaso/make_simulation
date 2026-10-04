import json,subprocess,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;O=R/'output';A=json.loads((R/'assets/audio/manifest.json').read_text());S=json.loads((R/'storyboard.json').read_text());D=json.loads((O/'trace.json').read_text())
def run(args):subprocess.run(args,check=True)
chapters=[dict(seconds=next(r['start'] for r in A if r['chapter']==i),title=c['title']) for i,c in enumerate(S['chapters'])];ends=[next(r['end'] for r in reversed(A) if r['chapter']==i) for i in range(8)];total=A[-1]['end']
run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(O/'blender/%04d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(O/'spatial.mp4')])
filters=(f'[4:v]setpts=PTS+{chapters[3]["seconds"]}/TB[sensor];'
 f'[0:v][sensor]overlay=0:0:enable=\'between(t,{chapters[3]["seconds"]},{ends[3]})\'[a];'
 f'[3:v]setpts=PTS+{chapters[5]["seconds"]}/TB[resample];'
 f'[a][resample]overlay=0:0:enable=\'between(t,{chapters[5]["seconds"]},{ends[5]})\'[b];'
 f'[5:v]setpts=PTS+{chapters[6]["seconds"]}/TB[local];'
 f'[b][local]overlay=0:0:enable=\'between(t,{chapters[6]["seconds"]},{ends[6]})\'[c];'
 f'[1:v]setpts=4*PTS+{chapters[6]["seconds"]}/TB,scale=1100:660,tpad=stop_mode=clone:stop_duration=40[space];'
 f'[c][space]overlay=100:230:enable=\'between(t,{chapters[6]["seconds"]},{ends[6]})\'[v]')
run(['ffmpeg','-v','error','-y','-i',str(O/'manim/videos/lesson/1080p30/AMCLLesson.mp4'),'-i',str(O/'spatial.mp4'),'-i',str(O/'narration.wav'),'-i',str(O/'manim/videos/lesson/1080p30/ResampleChapter.mp4'),'-i',str(O/'manim/videos/lesson/1080p30/SensorChapter.mp4'),'-i',str(O/'manim/videos/lesson/1080p30/LocalizationChapter.mp4'),'-filter_complex',filters,'-map','[v]','-map','2:a','-t',str(total),'-r','30','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-movflags','+faststart',str(O/'amcl_education_ko.mp4')])
im=Image.new('RGB',(1280,720),'#F7F9FC');d=ImageDraw.Draw(im);font='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
def text(x,y,t,size,color='#24344A'):d.text((x,y),t,font=ImageFont.truetype(font,size),fill=color)
text(60,50,'AMCL',106,'#188768');text(65,190,'지도는 있는데,',63);text(65,285,'나는 어디에?',72);text(65,570,'900개의 가설로 위치 찾기',37)
for a,b in D['walls']:
 a=(960+a[0]*42,330-a[1]*42);b=(960+b[0]*42,330-b[1]*42);d.line([a,b],fill='#697E94',width=6)
for p in D['initial'][::6]:
 x=960+p[0]*42;y=330-p[1]*42;d.line([(x,y),(x+8*math.cos(p[2]),y-8*math.sin(p[2]))],fill='#147DAD',width=2)
p=D['rows'][-1]['estimate'];x=960+p[0]*42;y=330-p[1]*42;d.ellipse((x-17,y-17,x+17,y+17),outline='#D97B20',width=6);text(865,535,'Known Map / Pose ?',30,'#147DAD');im.save(O/'thumbnail.png')
desc='SLAM 다음 편: 이번에는 지도가 이미 있습니다. AMCL이 입자로 위치와 방향의 가설을 표현하고, 오도메트리·LiDAR 관측·가중치·재표본추출을 통해 위치를 좁혀가는 과정을 설명합니다.\n\n'
for ch in chapters:
 t=int(ch['seconds']);desc+=f'{t//60:02d}:{t%60:02d} {ch["title"]}\n'
m=D['metrics'];desc+=f'\n교육용으로 직접 구현한 적응형 입자 필터입니다. 실제 로봇 데이터 또는 Nav2 AMCL 실행/성능 재현이 아닙니다. 정적 2D 지도, 36개 방향의 모의 LiDAR, 단순 상대 이동 잡음, 분석적으로 계산한 장애물 거리 기반 likelihood field, KLD 방식 입자 수 조절을 사용합니다. 지도는 고정하며 새로 작성하지 않습니다. 지도 표시는 점유 칸이지만 센서 점수는 연속 선분 거리로 계산하는 단순화입니다.\n\n입자는 빈 공간 전체에서 초기화합니다. 측정값 생성과 평가에 사용한 기준 Pose를 추정기에 입력하지 않습니다. 지도 전체의 위치를 모르는 시작을 보여주는 예이며, 실제로는 초기 Pose 주변에서 시작할 수도 있습니다. cmd_vel은 명령이며 이 예제의 이동 입력은 오도메트리입니다.\n\n단일 합성 실험(seed 42 / 관측 seed 6), 22회 갱신 결과: 위치 오차 {m["final_position_error_m"]*100:.2f} cm, 방향 오차 {m["final_heading_error_deg"]:.2f}도. 입자 수 900 → 399 → 180. 관측 갱신을 끈 비교의 최종 위치 오차 {m["no_sensor_final_error_m"]:.2f} m. 일반적인 로봇 성능 수치가 아닙니다. 전역 분포가 여러 봉우리를 가지면 평균 Pose가 부정확할 수 있으며, 여기서는 수렴 후의 가중 평균과 원형 평균 방향을 표시합니다. 실제 시스템의 군집 선택, 회복 입자 주입, TF, 센서 오프셋, 동적 물체 처리는 구현하지 않았습니다.\n\nBlender 공간 영상은 같은 기록을 느리게 재생한 것입니다. 파랑은 입자, 초록 고리는 추정 위치, AMR 모델은 기준 위치입니다. 한국어 합성 음성 및 Whisper 기반 자막 정렬을 사용했습니다.\n\n이전 편 SLAM\nhttps://www.youtube.com/watch?v=VGIooUDrPbM\n\n공식 참고 자료\nhttps://docs.nav2.org/rolling/configuration_and_development/configuration_guide/others/configuring_amcl/\nhttps://github.com/ros-navigation/navigation2/tree/main/nav2_amcl\n\n#AMCL #SLAM #로봇 #자율주행 #ParticleFilter #ROS2\n'
package=dict(video='../output/amcl_education_ko.mp4',title='AMCL은 어떻게 로봇의 위치를 찾을까? | SLAM 다음 편',description=desc,privacy='public',channel_id='UCKT_GQPU4i_wmtE-b_6wa8A',captions='../output/subtitles.ko.srt',caption_language='ko',thumbnail='../output/thumbnail.png',made_for_kids=False,contains_synthetic_media=False,tags=['AMCL','SLAM','Particle Filter','로봇','ROS2','Nav2','Manim','Blender'],chapters=chapters)
(R/'publish/package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2));(O/'youtube_description.txt').write_text(desc);(O/'timeline.json').write_text(json.dumps(dict(chapters=chapters,ends=ends,duration=total,blender=dict(start=chapters[6]['seconds'],end=ends[6],speed='4x slow; 900-particle initial hold, then 22 recorded updates; final hold')),ensure_ascii=False,indent=2));print('Finished',total)
