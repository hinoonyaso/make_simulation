from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent;V=ROOT.parent/'simulation_v3';OUT=V/'output'
bg=Image.new('RGB',(1280,720),'#F7F9FC');d=ImageDraw.Draw(bg)
font='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
f=lambda n:ImageFont.truetype(font,n)
d.text((55,48),'로봇은 픽셀을 어떻게',font=f(58),fill='#202D43')
d.text((55,123),'3D 위치로 바꿀까?',font=f(65),fill='#2676D5')
scene=Image.open(OUT/'blender/world/0150.png').convert('RGB').resize((660,424));bg.paste(scene,(20,250));d=ImageDraw.Draw(bg)
d.text((730,280),'PIXEL + DEPTH',font=f(39),fill='#202D43')
d.text((775,365),'→ XYZ',font=f(67),fill='#2676D5')
d.rounded_rectangle((715,495,1210,568),radius=18,fill='#202D43');d.text((747,508),'노이즈 · 보정 오류 실험',font=f(31),fill='white')
d.text((738,608),'Manim + Blender',font=f(30),fill='#65738A')
bg.save(OUT/'thumbnail.jpg',quality=94)
doc=json.loads((V/'storyboard.json').read_text());timeline=json.loads((OUT/'render_timeline.json').read_text())
desc='픽셀 좌표와 깊이 Z, 카메라 내부 파라미터 K로 3D 표면 위치를 구하는 과정을 Manim 수식과 Blender 시뮬레이션으로 설명합니다.\n\n움직이는 장면 → 카메라 RGB·깊이 관측 → 역투영 → 실제 표면점과 오차 비교\nX = (u − cx) Z / fx, Y = (v − cy) Z / fy\n\n'
for row,ch in zip(timeline,doc['chapters']):
 s=int(row['start']+1e-6);desc+=f"{s//60:02}:{s%60:02} {ch['title']}\n"
desc+='''
[실험 조건과 결과]
합성 핀홀 카메라, 160×120 관측, fx=fy=150 px, 주점 (79.5,59.5), 이상적인 물체 구분을 가정합니다. 깊이는 광선의 직선거리가 아닌 광학축 Z 성분입니다. 복원 대상은 물체 중심이 아니라 선택 픽셀이 보는 표면점입니다.

같은 10초 경로의 301개 표본으로 계산한 3D 위치 RMSE:
• 이상적인 기준: 약 0 mm
• 깊이 잡음 σZ=0.04 m: 40.33 mm
• 복원용 fx만 실제 값의 80%로 변경: 59.99 mm
• 정확한 보정값 복구: 약 0 mm
난수 seed: 20260916

이 수치는 자체 합성 실험 결과이며 실제 깊이 카메라의 정확도를 뜻하지 않습니다. 렌즈 왜곡과 실제 센서의 모든 오차는 구현하지 않았습니다. 영상은 계산된 실험 기록을 재생하며, 카메라 좌표를 로봇에서 사용하려면 좌표 변환과 동작 계획이 별도로 필요합니다.

한국어 합성 음성과 Whisper로 정렬한 교정 자막을 사용했습니다.

[참고 자료]
OpenCV Camera Calibration and 3D Reconstruction
https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html
ROS REP-103 좌표계 규약
https://www.ros.org/reps/rep-0103.html

#로보틱스 #컴퓨터비전 #DepthCamera #Manim #Blender
'''
p=dict(video='../simulation_v3/output/pixel_depth_simulation_ko_v3.mp4',title='픽셀과 깊이로 3D 위치를 구하는 법 | 카메라 역투영 시뮬레이션',description=desc,privacy='public',channel_id='UCKT_GQPU4i_wmtE-b_6wa8A',captions='../simulation_v3/output/subtitles.ko.srt',caption_language='ko',thumbnail='../simulation_v3/output/thumbnail.jpg',made_for_kids=False,contains_synthetic_media=False,tags=['로보틱스','컴퓨터비전','Depth Camera','카메라 보정','역투영','Manim','Blender','3D 시뮬레이션'])
(ROOT/'package.json').write_text(json.dumps(p,ensure_ascii=False,indent=2));(OUT/'youtube_description.txt').write_text(desc)
