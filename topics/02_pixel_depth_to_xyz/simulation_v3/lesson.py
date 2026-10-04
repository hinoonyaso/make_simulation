"""Focused Manim presentation; the compositor supplies measured spatial evidence."""
import json
from pathlib import Path
from manim import *
ROOT=Path(__file__).resolve().parent
BG='#F7F9FC'; INK='#202D43'; BLUE='#2676D5'; MUTED='#65738A'; RED='#D34F55'; GREEN='#198F70'
def at(x,y):return [(x-960)/135,(540-y)/135,0]
def text(s,x,y,size=28,color=INK):return Text(s,font='NanumGothic',font_size=size,color=color).move_to(at(x,y))
def eq(s,x,y,size=40):return MathTex(s,font_size=size,color=INK).move_to(at(x,y))
class PixelDepthSimulation(Scene):
 def construct(self):
  self.camera.background_color=BG
  doc=json.loads((ROOT/'storyboard.json').read_text());records=json.loads((ROOT/'assets/audio/manifest.json').read_text());timeline=[]
  self.add_sound(str(ROOT/'output/narration.wav'))
  for ci,ch in enumerate(doc['chapters']):
   rs=[r for r in records if r['chapter']==ci];start=rs[0]['start'];end=rs[-1]['end'];self.clear()
   self.add(text('PIXEL + DEPTH → 3D XYZ',385,65,21,BLUE),text(f'{ci+1:02} / 08',1780,65,20,MUTED))
   title=text(ch['title'],960,143,38);self.add(title)
   self.add(Line(at(70,200),at(1850,200),color='#DDE5EF'))
   if ci<7:
    self.add(text('3D 장면 · 합성 핀홀 카메라',500,239,23),text('● 실제 표면     ○ 복원 위치',500,825,23))
   items=[]
   if ci==0:
    items=[text('장면을 관측하고',1430,310,34),text('픽셀 + 깊이를 얻고',1430,475,34,BLUE),text('표면의 XYZ를 복원',1430,640,34,GREEN)]
   elif ci==1:
    self.add(text('카메라 RGB · 선택한 픽셀',1430,260,26,BLUE))
    items=[text('픽셀 좌표 ≠ 공간 좌표',1430,785,28),text('영역의 가운데 픽셀을 선택',1430,845,23,MUTED)]
   elif ci==2:
    self.add(text('장면 교차로 만든 깊이 Z',1430,260,26,BLUE))
    items=[eq(r'Z \neq \|P\|',1430,800),text('광학축 성분 ≠ 직선거리',1430,862,25,MUTED)]
   elif ci==3:
    items=[eq(r'x_n=\frac{u-c_x}{f_x},\quad y_n=\frac{v-c_y}{f_y}',1430,365,37),eq(r'\mathbf r=(x_n,\ y_n,\ 1)',1430,500,37),eq(r'\mathbf P=Z\mathbf r=(X,Y,Z)',1430,635,37),text('모델이 일치하는 이상적 기준',1430,835,23,MUTED)]
   elif ci==4:
    items=[eq(r'Z_{obs}=Z+\epsilon',1430,315),eq(r'\epsilon\sim\mathcal N(0,0.04^2)\;[m]',1430,400,32),eq(r'\Delta\mathbf P=\epsilon\,(x_n,y_n,1)',1430,500,35)]
   elif ci==5:
    items=[eq(r'f_x:150\rightarrow120\;[px]',1430,310),eq(r'\hat X=\frac{(u-c_x)Z}{0.8f_x}=1.25X',1430,420,35),text('X의 크기가 25% 확대',1430,515,29,RED)]
   elif ci==6:
    items=[text('301개 표본 · 같은 경로',1430,300,28)]
    metrics=json.loads((ROOT/'output/trace.json').read_text())['metrics']
    for i,(k,label,col) in enumerate([('ideal','기준',GREEN),('noise','깊이 잡음',RED),('bad_k','잘못된 fx',RED),('correct','보정 복구',BLUE)]):
     val=metrics[k]['rmse_mm'];items.append(text(f'{label}   {val:.2f} mm',1430,415+105*i,30,col))
    self.add(text('3D 위치 RMSE',1430,865,22,MUTED))
   else:
    items=[text('같은 픽셀의 (u, v) + 깊이 Z + 내부 행렬 K',960,330,34,BLUE),eq(r'\mathbf P_{camera}=ZK^{-1}[u,v,1]^T',960,485,49),text('카메라 좌표 → TF2 → 로봇 기준 좌표 → 동작 계획',960,670,31,GREEN),text('합성 실험: 렌즈 왜곡·실제 센서의 모든 오차는 미포함',960,835,25,MUTED)]
   # Progressive mathematical reveals; no permanent dashboard.
   for item in items:
    self.play(FadeIn(item,shift=UP*.1),run_time=.4)
    self.wait(.3)
   self.wait(max(0,end-self.time))
   timeline.append(dict(chapter=ci,start=start,end=end,render_end=self.time))
  (ROOT/'output/render_timeline.json').write_text(json.dumps(timeline,indent=2))
