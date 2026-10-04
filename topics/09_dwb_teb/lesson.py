from pathlib import Path
import json,numpy as np
from manim import *
R=Path(__file__).resolve().parent;D=json.loads((R/'output/trace.json').read_text());A=json.loads((R/'assets/audio/manifest.json').read_text());S=json.loads((R/'storyboard.json').read_text());BG='#F7F9FC';INK='#26364A';BLUE='#147DAD';GREEN='#198868';PURPLE='#8A66B2';RED='#B75057';ORANGE='#D58525';GRAY='#ACB7C5';MUTED='#738195'
def txt(s,size=25,color=INK,width=None):
 t=Text(s,font='NanumGothic',font_size=size,color=color)
 if width and t.width>width:t.scale_to_fit_width(width)
 return t
def xy(p):return np.array([(p[0]+.2)*1.5-2.5,p[1]*1.5+.1,0])
def pathline(points,color=GREEN,width=4):return VMobject(color=color,stroke_width=width).set_points_as_corners([xy(p) for p in points])
def robot(p):return VGroup(Circle(.22*1.5,color=BLUE,fill_color=WHITE,fill_opacity=1).move_to(xy(p)),Arrow(xy(p),xy(p)+.5*np.array([np.cos(p[2]),np.sin(p[2]),0]),buff=0,color=BLUE,stroke_width=3,max_tip_length_to_length_ratio=.3))
def band(poses,color=PURPLE):
 g=VGroup(pathline(poses,color,5))
 for p in poses:g.add(Dot(xy(p),radius=.07,color=color),Line(xy(p),xy(p)+.23*np.array([np.cos(p[2]),np.sin(p[2]),0]),color=color,stroke_width=3))
 return g
class ControllerComparison(Scene):
 def construct(self):
  self.camera.background_color=BG;self.events=[];hero=D['hero'];dw=hero['dwb']['detail'];tb=hero['teb']['detail']
  for ci,ch in enumerate(S['chapters']):
   self.clear();self.add(txt(f'{ci+1:02d} / 08   DWB vs TEB',18,MUTED).to_corner(UL,buff=.35),txt(ch['title'],33,width=12.7).move_to([0,3.05,0]),Line([-6.6,2.57,0],[6.6,2.57,0],color='#DAE2EB'),txt('교육용 모형 · 실제 플러그인 실행 아님 · 이상적 위치·장애물 지도',16,MUTED).move_to([0,-2.86,0]));subtitle=None
   def say(li,action=None,seconds=3):
    nonlocal subtitle
    rec=next(a for a in A if a['chapter']==ci and a['line']==li)
    if subtitle:self.remove(subtitle)
    subtitle=txt(rec['caption'],24,width=13).move_to([0,-3.42,0]);self.add(subtitle)
    if action:action(min(seconds,rec['end']-self.time-.1))
    if rec['end']>self.time:self.wait(rec['end']-self.time)
   def side(lines,y=0,size=25):
    g=VGroup(*[txt(s,size,width=4.1) for s in lines]).arrange(DOWN,buff=.30).move_to([4.25,y,0]);self.add(g);return g
   def play(a):return lambda t:self.play(a,run_time=t)
   def corridor(obstacle=True):
    g=VGroup(Line(xy([-2.7,1.25]),xy([2.3,1.25]),color='#586B80',stroke_width=13),Line(xy([-2.7,-1.25]),xy([2.3,-1.25]),color='#586B80',stroke_width=13),DashedLine(xy([-2.7,0]),xy([2.3,0]),color=GRAY,stroke_width=3),txt('Global Path',17,MUTED).move_to(xy([1.5,-.25])))
    if obstacle:g.add(Circle(D['obstacle_radius']*1.5,color=RED,fill_color=RED,fill_opacity=.65).move_to(xy(D['obstacle'])))
    self.add(g);return g
   if ci in [1,2,4,5,6]:self.add(txt('계산 예시 Pose = (−1.25 m, 0 m, 0 rad)',16,MUTED).move_to([-2.3,2.23,0]))
   if ci==0:
    corridor();self.add(robot(hero['dwb']['pose']));side(['같은 출발·목표','같은 Global Path','같은 장애물 지도','다른 계산 방식']);say(0);say(1)
    self.clear();self.add(txt('TEB의 ROS 2 지원 맥락',34).move_to([0,3.05,0]),txt('원 저장소에서 확인 · 2026-09-22',23,MUTED).move_to([0,2,0]));self.add(VGroup(txt('ros2-master / humble-devel',32,BLUE),txt('nav2_core::Controller 플러그인 선언 확인',27),txt('README에는 이전 Dashing 설명이 남아 있음',25),txt('최신 배포판 빌드·동작 호환성을 보장하지 않음',25,ORANGE)).arrange(DOWN,buff=.45).move_to([0,.2,0]));say(2);say(3)
   elif ci==1:
    corridor();self.add(robot(hero['dwb']['pose']));side(['v: 전진 속도 [m/s]','ω: 회전 속도 [rad/s]','하나의 후보 = (v, ω)','짧은 미래 = 2.0 s'],size=24);say(0)
    g=VGroup(*[pathline(c['trajectory'],GRAY,2) for c in dw['candidates'][::5]]);say(1,play(LaggedStart(*[Create(x) for x in g],lag_ratio=.02)),6);say(2)
   elif ci==2:
    corridor();self.add(robot(hero['dwb']['pose']));valid=sorted([c for c in dw['candidates'] if c['valid']],key=lambda c:c['score']);examples=[valid[0],valid[len(valid)//3],valid[-1]];lines=VGroup(*[pathline(c['trajectory'],GREEN if i==0 else GRAY,5 if i==0 else 3) for i,c in enumerate(examples)]);self.add(lines);panel=side(['Critics → 총비용','Path / Goal / Obstacle','유효하지 않음 → 제외','작은 총비용 → 선택'],size=24);say(0)
    self.add(txt('J = w₁Cpath + w₂Cgoal + w₃Cobs + …',25).move_to([-2.35,-2.28,0]));say(1,play(Indicate(lines[0],color=GREEN)),3);self.remove(panel);labels=['v       ω       J']+[f'{c["v"]:.2f}   {c["w"]:+.2f}   {c["score"]:.2f}' for c in examples];side(['모형의 계산 결과',*labels,'첫 행: 최소 비용 선택'],size=23);say(2)
   elif ci==3:
    side(['(v, ω)','↓ 0.2 s 실행','새 Pose / 주변 정보','↓','Sample → Score','→ Select → Move'],size=24);say(0);say(1);say(2)
   elif ci==4:
    corridor(False);initial=tb['iterations'][0];self.add(band(initial['poses']));side(['Pᵢ = (xᵢ, yᵢ, θᵢ)','ΔTᵢ > 0','포즈와 시간 간격','둘 다 최적화 변수']);say(0)
    dt=initial['dt'];labels=VGroup(*[txt(f'ΔT{i} = {dt[i]:.2f}s',18,PURPLE).move_to([x,-1.2,0]) for i,x in zip([0,4,8],[-4.5,-2.5,-.5])]);say(1,play(FadeIn(labels)),3);say(2)
   elif ci==5:
    corridor();b=band(tb['iterations'][0]['poses']);self.add(b);panel=side(['초기 Band',f'J = {tb["iterations"][0]["objective"]:.2f}','점: Pose','연결: 이동 구간','아직 실행한 길 아님'],size=24);say(0)
    def optimize(seconds):
     nonlocal b,panel
     hist=tb['iterations'][1:];frames=round(seconds*30)
     for i,row in enumerate(hist):
      self.remove(b,panel);b=band(row['poses']);self.add(b);panel=side(['최적화 계산 기록',f'갱신 {i+1}',f'J = {row["objective"]:.2f}',f'Σ ΔT = {sum(row["dt"]):.2f}s','예측 궤적'],size=24);self.events.append(dict(chapter=ci,video_time=self.time,optimizer_snapshot=i+1));self.wait((round((i+1)*frames/len(hist))-round(i*frames/len(hist)))/30)
    say(1,optimize,10);say(2)
   elif ci==6:
    corridor();self.add(band(tb['poses']));v,w=hero['teb']['cmd'];panel=side(['Jtime: 시간','Jobs: 장애물 거리','Jkinematics: 운동 제약','Jvia: 경유점 참조','+ 추가 항목'],size=24);self.add(txt('J = Jtime + Jobs + Jkinematics + Jvia + …',23,width=8).move_to([-2.3,-2.35,0]));say(0);say(1)
    self.remove(panel);side(['최적화 궤적','↓ 첫 구간의 명령',f'v = {v:.2f} m/s',f'ω = {w:.2f} rad/s','다음 상태에서 재계산'],size=24);say(2)
   else:
    self.add(txt('DWB',36,BLUE).move_to([-3.3,1.98,0]),txt('TEB',36,PURPLE).move_to([3.3,1.98,0]));left=VGroup(*[txt(s,25,width=5.8) for s in ['Velocity Samples','↓ Rollout → Score','Best cmd_vel']]).arrange(DOWN,buff=.2).move_to([-3.3,.55,0]);right=VGroup(*[txt(s,25,width=5.8) for s in ['Poses + ΔT','↓ Optimization','Current cmd_vel']]).arrange(DOWN,buff=.2).move_to([3.3,.55,0]);self.add(left,right);say(0,play(Indicate(left,color=BLUE)),2);say(1,play(Indicate(right,color=PURPLE)),2)
    self.remove(left,right);self.add(txt('지역 속도 탐색',27,BLUE).move_to([-3.3,1.2,0]),txt('시간 포함 궤적 최적화',27,PURPLE).move_to([3.3,1.2,0]));say(2);say(3)
  (R/'output/render_events.json').write_text(json.dumps(self.events,ensure_ascii=False,indent=2))
