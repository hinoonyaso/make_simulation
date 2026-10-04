from pathlib import Path
import json,numpy as np
from manim import *
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'output/trace.json').read_text());A=json.loads((ROOT/'assets/audio/manifest.json').read_text());ST=json.loads((ROOT/'storyboard.json').read_text())
BG='#F7F9FC';INK='#24344A';BLUE='#147DAD';ORANGE='#D97B20';GREEN='#188768';MUTED='#738195'
def txt(s,size=27,color=INK):return Text(s,font='NanumGothic',font_size=size,color=color)
def pos(p):return np.array([p[0]*.65-2.15,p[1]*.65-.4,0])
def mapview():
 g=VGroup()
 # Explicit occupancy cells, fixed known map throughout this episode.
 for a,b in D['walls']:
  a,b=np.array(a),np.array(b)
  for p in np.linspace(a,b,int(np.linalg.norm(b-a)/.15)+1):g.add(Square(.09,stroke_width=0,fill_color='#697E94',fill_opacity=1).move_to(pos(p)))
 return g

def marker(p,color=BLUE,size=.095):
 a=p[2];c=pos(p);v=np.array([np.cos(a),np.sin(a),0]);n=np.array([-np.sin(a),np.cos(a),0])
 return VMobject(color=color,stroke_width=2.3).set_points_as_corners([c-size*v/2+size*n/3,c+size*v/2,c-size*v/2-size*n/3])
def particles(poses,weights=None):
 # Entire population is shown; multiplicity naturally overlaps after resampling.
 g=VGroup()
 for i,p in enumerate(poses):
  q=marker(p)
  if weights is not None:
   v=float(np.sqrt(weights[i]/max(weights)));q.set_color(interpolate_color(ManimColor('#C8D3DF'),ManimColor(ORANGE),v));q.set_stroke(opacity=.2+.8*v,width=1.2+3*v)
  g.add(q)
 return g

def rays(p,z,color):
 a=np.array(D['angles'])+p[2];pts=np.array(p[:2])+np.array(z)[:,None]*np.c_[np.cos(a),np.sin(a)]
 g=VGroup();start=pos(p)
 for q in pts:
  end=pos(q);delta=end-start;lo=0.;hi=1.
  for axis,lower,upper in [(0,-6.3,1.8),(1,-2.4,2.35)]:
   if abs(delta[axis])<1e-10:
    if not lower<=start[axis]<=upper:hi=-1
   else:
    t0,t1=sorted([(lower-start[axis])/delta[axis],(upper-start[axis])/delta[axis]]);lo=max(lo,t0);hi=min(hi,t1)
  if lo<hi:g.add(Line(start+lo*delta,start+hi*delta,color=color,stroke_width=1.1,stroke_opacity=.5))
  if -6.3<=end[0]<=1.8 and -2.4<=end[1]<=2.35:g.add(Dot(end,radius=.035,color=color))
 return g

class AMCLLesson(Scene):
 def construct(self):
  self.camera.background_color=BG
  for ci,ch in enumerate(ST['chapters']):
   if hasattr(self,'only_chapter') and ci!=self.only_chapter:continue
   offset=next(r['start'] for r in A if r['chapter']==ci) if hasattr(self,'only_chapter') else 0
   self.clear();self.add(txt(f'{ci+1:02d} / 08   AMCL',19,MUTED).to_corner(UL,buff=.35));self.add(txt(ch['title'],35).move_to([0,3.05,0]));self.add(Line([-6.6,2.55,0],[6.6,2.55,0],color='#DCE4ED'))
   self.add(txt('교육용 모의 실험 · 지도는 고정 · m / rad',16,MUTED).move_to([0,-2.85,0]));sub=None
   def say(li,anim=None,run=2):
    nonlocal sub
    rec=next(r for r in A if r['chapter']==ci and r['line']==li)
    if sub:self.remove(sub)
    sub=txt(rec['caption'],25).move_to([0,-3.42,0]);self.add(sub)
    if anim:self.play(anim,run_time=run)
    remaining=rec['end']-offset-self.time
    if remaining>0:self.wait(remaining)
   def side(lines):
    g=VGroup(*[txt(s,25) for s in lines]).arrange(DOWN,buff=.38).move_to([4.35,.05,0]);self.add(g);return g
   row=D['rows'][0]
   if ci==0:
    self.add(mapview());q=txt('Robot ?',38,ORANGE).move_to(pos([0,0]));self.add(q)
    s=side(['SLAM','Map ? + Pose ?','','AMCL','Map ✓ + Pose ?'])
    say(0);say(1);say(2)
   elif ci==1:
    self.add(mapview());cloud=particles(D['initial']);s=side(['Particle','(x, y, θ)','↓','위치 + 방향','900개 가설'])
    say(0,FadeIn(cloud),3);say(1);say(2)
   elif ci==2:
    self.add(mapview());cloud=particles(row['prior']);self.add(cloud);s=side(['Odometry','↓','Motion model','+ noise','↓','Predicted particles'])
    say(0,Transform(cloud,particles(row['predicted'])),4);say(1);say(2,Indicate(cloud,color=ORANGE),2)
   elif ci==3:
    self.add(mapview());p=np.array(row['predicted']);w=np.array(row['weights']);hi=int(w.argmax());lo=int(np.argsort(w)[len(w)//2]);good=p[hi];bad=p[lo]
    # One observed scan is transformed under two hypotheses, not two new measurements.
    self.add(marker(good,GREEN,.28));ray=rays(good,row['scan'],BLUE);self.add(ray)
    s=side(['같은 관측 zₜ','표시 영역 내 관측','↓','지도와 비교','벽 근처 끝점'])
    say(0);other=rays(bad,row['scan'],ORANGE);say(1,AnimationGroup(FadeOut(ray),FadeIn(other)),3)
    self.remove(s);side(['Likelihood field','관측 끝점','↕ 거리','지도 장애물'])
    ray=rays(good,row['scan'],BLUE);say(2,AnimationGroup(FadeOut(other),FadeIn(ray)),3)
   elif ci==4:
    self.add(mapview());cloud=particles(row['predicted']);self.add(cloud)
    side(['wᵢ ∝ p(zₜ | xᵢ, m)','zₜ: 관측','xᵢ: 위치 후보','m: 기존 지도','밝고 굵게 = 높은 w'])
    say(0,Transform(cloud,particles(row['predicted'],row['weights'])),3);say(1);say(2)
   elif ci==5:
    self.add(mapview());cloud=particles(row['predicted'],row['weights']);self.add(cloud)
    counts=np.bincount(row['parents'],minlength=len(row['predicted']));hi=int(counts.argmax())
    s=side(['Weighted sampling','900개 → 399개',f'가장 많이 선택: {counts[hi]}회','복제는 같은 Pose'])
    say(0)
    selected=particles(row['resampled']);say(1,AnimationGroup(FadeOut(cloud),FadeIn(selected),lag_ratio=.2),4);say(2)
    self.remove(s);side(['Adaptive','900 → 399 → 180','분포가 차지한 구간','↓','필요 입자 수'])
    say(3)
   elif ci==6:
    # Blender spatial playback is composited into the left viewport.
    m=D['metrics'];side(['파랑: 입자','초록: 추정 Pose','AMR: 기준 Pose',f"최종 위치 오차 {m['final_position_error_m']*100:.1f} cm",'최종 입자 180개'])
    say(0);say(1);say(2)
   else:
    left=VGroup(txt('SLAM',42,BLUE),txt('Map ? + Pose ?',30),txt('↓',32),txt('지도 + 위치 추정',30)).arrange(DOWN,buff=.3).move_to([-3.25,.3,0])
    right=VGroup(txt('AMCL',42,GREEN),txt('Known Map + Sensor',29),txt('+ Odometry',26),txt('↓',32),txt('위치 + 불확실성',30)).arrange(DOWN,buff=.27).move_to([3.3,.3,0]);self.add(left,right,Line([0,2,0],[0,-1.8,0],color='#DCE4ED'))
    say(0);say(1);self.add(txt('Motion → Sensor → Weight → Resample',28).move_to([0,-2.3,0]));say(2)

class ResampleChapter(AMCLLesson):
 only_chapter=5

class SensorChapter(AMCLLesson):
 only_chapter=3

class LocalizationChapter(AMCLLesson):
 only_chapter=6
