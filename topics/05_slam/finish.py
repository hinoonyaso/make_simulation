import json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;O=ROOT/'output';A=json.loads((ROOT/'assets/audio/manifest.json').read_text());S=json.loads((ROOT/'storyboard.json').read_text())
def run(args):subprocess.run(args,check=True)
chapters=[{'seconds':next(r['start'] for r in A if r['chapter']==i),'title':c['title']} for i,c in enumerate(S['chapters'])]
ends=[next(r['end'] for r in reversed(A) if r['chapter']==i) for i in range(8)]
for mode in ['scan','motion']:
 run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(O/f'blender/{mode}/%04d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(O/f'{mode}.mp4')])
base=O/'manim/videos/lesson/1080p30/SlamLesson.mp4'
# Each sensor/motion clip plays once over its narration window, then holds its final frame.
start1=chapters[1]['seconds'];start3=chapters[3]['seconds'];total=A[-1]['end']
filters=(f'[1:v]scale=1100:660[intro];[0:v][intro]overlay=100:230:enable=\'lt(t,{ends[0]})\'[a];'
 f'[2:v]setpts=4*PTS+{start1}/TB,scale=1100:660,tpad=stop_mode=clone:stop_duration=40[scan];'
 f'[a][scan]overlay=100:230:enable=\'between(t,{start1},{ends[1]})\'[b];'
 f'[3:v]setpts=6*PTS+{start3}/TB,scale=1100:660,tpad=stop_mode=clone:stop_duration=40[motion];'
 f'[b][motion]overlay=100:230:enable=\'between(t,{start3},{ends[3]})\'[c];'
 f'[5:v]setpts=PTS+{chapters[6]["seconds"]}/TB[map];'
 f'[c][map]overlay=0:0:enable=\'between(t,{chapters[6]["seconds"]},{ends[6]})\'[v]')
run(['ffmpeg','-v','error','-y','-i',str(base),'-loop','1','-framerate','30','-i',str(O/'blender/intro.png'),'-i',str(O/'scan.mp4'),'-i',str(O/'motion.mp4'),'-i',str(O/'narration.wav'),'-i',str(O/'manim/videos/lesson/1080p30/MapChapter.mp4'),'-filter_complex',filters,'-map','[v]','-map','4:a','-t',str(total),'-r','30','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-movflags','+faststart',str(O/'slam_education_ko.mp4')])
im=Image.new('RGB',(1280,720),'#F7F9FC');d=ImageDraw.Draw(im);font='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
def text(x,y,t,size,color='#233247'):d.text((x,y),t,font=ImageFont.truetype(font,size),fill=color)
text(65,55,'SLAM',104,'#147DAD');text(65,185,'지도와 내 위치를',64);text(65,270,'동시에 찾는 법',72)
text(70,580,'LiDAR  +  이동  →  위치와 지도',36)
trace=json.loads((O/'trace.json').read_text())
for p in trace['scans'][0]:
 x=950+p[0]*43;y=340-p[1]*43;d.ellipse((x-3,y-3,x+3,y+3),fill='#147DAD')
d.rounded_rectangle((915,310,970,355),radius=10,fill='#198465');d.polygon([(970,317),(990,331),(970,345)],fill='#198465');text(850,520,'SCAN → MATCH',27,'#DC781A');im.save(O/'thumbnail.png')
desc='SLAM은 어떻게 지도와 로봇 위치를 동시에 찾을까요? LiDAR 관측, 오도메트리, 스캔 정합, 위치 보정, 점유 지도 갱신을 8개 장면으로 설명합니다.\n\n'
for ch in chapters:
 t=int(ch['seconds']);desc+=f'{t//60:02d}:{t%60:02d} {ch["title"]}\n'
desc+='\n직접 제작한 교육용 모의 실험입니다. 2D 정적 벽, 240개 광선, 거리 잡음 표준편차 1.2 cm, 오차가 있는 이동량, scan-to-scan ICP를 사용했습니다. 실제 AMR 시험이나 특정 SLAM 제품의 성능이 아닙니다. 첫 포즈를 지도 원점으로 선택합니다. 정합에는 정답 위치를 넣지 않으며 정답은 관측 생성과 오차 평가에만 사용합니다. 점유 지도는 통과/끝점 근거를 누적한 단순 log-odds 예제입니다. 루프 폐쇄, Graph SLAM, 동적 장애물, 실제 엔코더 모델은 포함하지 않습니다.\n\n16개 포즈, seed 21의 위치 RMSE: 오도메트리만 57.57 cm / 스캔 정합 7.41 cm. 단일 합성 실험이며 일반 성능을 의미하지 않습니다. Blender 공간 영상은 저장된 모의 관측의 오프라인 재생입니다. 한국어 합성 내레이션과 Whisper 정렬 자막을 사용했습니다.\n\n참고: 관측 정합과 지도 갱신의 기본 구조\nhttps://google-cartographer-ros.readthedocs.io/en/latest/algo_walkthrough.html\n이 영상의 작은 ICP 예제는 Cartographer 구현 재현이 아닙니다.\n\n#SLAM #LiDAR #로봇 #자율주행 #Manim #Blender\n'
package=dict(video='../output/slam_education_ko.mp4',title='SLAM은 어떻게 지도와 로봇 위치를 동시에 찾을까?',description=desc,privacy='private',channel_id='UCKT_GQPU4i_wmtE-b_6wa8A',captions='../output/subtitles.ko.srt',caption_language='ko',thumbnail='../output/thumbnail.png',made_for_kids=False,contains_synthetic_media=False,tags=['SLAM','LiDAR','AMR','로봇','스캔 정합','Manim','Blender'],chapters=chapters)
(ROOT/'publish/package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2));(O/'youtube_description.txt').write_text(desc)
(O/'timeline.json').write_text(json.dumps({'chapters':chapters,'ends':ends,'duration':total,'blender':{'intro':[0,ends[0]],'scan':[start1,ends[1]],'motion':[start3,ends[3]],'note':'clips play once then hold; motion visualization time is not real-time sensing'}},ensure_ascii=False,indent=2))
print('Finished',total)
