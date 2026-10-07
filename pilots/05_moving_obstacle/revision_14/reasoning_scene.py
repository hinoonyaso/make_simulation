"""Observation -> wheel quantities -> mean/difference -> response, single manifest."""
import json,sys,math
from pathlib import Path
import numpy as np
from manim import *
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[2]/'core/manim-robotics-education-skill/templates'))
from manim_kit import P,BeatClock,txt,apply_theme
DOC=json.loads((H/'visual_manifest.json').read_text())
D=json.loads((H.parent/'revision_06/data/baseline_planner_on.json').read_text())
CASES={k:json.loads((H/'data'/f'baseline_{k}.json').read_text()) for k in ['equal','left','spin','stop']}
def label(s,size=32,color=P.fg):return txt(s,size=size,color=color)
def W(p):return np.array([p[0]*2.5,p[1]*2.5-.2,0])
def line(points,color):return VMobject(stroke_color=color,stroke_width=5).set_points_as_corners([W(p) for p in points])
def wheelbot():
 body=RoundedRectangle(width=1.25,height=1.55,corner_radius=.1,color=P.fg,fill_color='#394455',fill_opacity=1)
 wheels=VGroup(*[RoundedRectangle(width=.22,height=.65,corner_radius=.05,color=P.fg,fill_opacity=1).shift([x,0,0]) for x in [-.82,.82]])
 return VGroup(body,wheels)
class WheelDiscovery(Scene):
 def construct(self):
  apply_theme(self)
  bot=wheelbot().move_to([-3.7,.1,0]);title=label('길을 그렸는데, 어떻게 움직일까?',39).move_to([0,3.25,0])
  front=label('앞 ↑',26,P.muted).next_to(bot,UP,buff=.35)
  self.add(bot,front,title)
  active=VGroup();values=VGroup();arrows=VGroup()
  def swap(clock,group):
   nonlocal active
   persistent={id(m) for g in [bot,front,title,values,arrows] for m in g.get_family()}
   stale=[m for m in self.mobjects if id(m) not in persistent]
   if stale:clock.play(*[FadeOut(m) for m in stale],run_time=.35)
   active=group;clock.play(FadeIn(active),run_time=.65)
  def goals(clock,l,r):
   nonlocal values,arrows
   nxt=VGroup(label(f'왼쪽 {l:+.2f} m/s',28),label(f'오른쪽 {r:+.2f} m/s',28,P.sensor)).arrange(DOWN,buff=.2).move_to([-3.7,-1.55,0])
   arr=VGroup(*[Arrow([x,.15,0],[x,.15+(v*5 if abs(v)>.01 else .02),0],buff=0,color=P.sensor,stroke_width=6) for x,v in [(-4.52,l),(-2.88,r)]])
   if len(values):clock.play(Transform(values,nxt),Transform(arrows,arr),run_time=.65)
   else:values=nxt;arrows=arr;clock.play(FadeIn(values),GrowArrow(arr[0]),GrowArrow(arr[1]),run_time=.65)
  for beat in DOC['beats']:
   bid=beat['id'];kind=beat['state_change'];sec=beat['sec']
   self.next_section(bid,skip_animations=type(self).__name__=='FixedMeanPatch' and bid!='B13')
   with BeatClock(self,sec) as c:
    heading={
     'question':'길을 그렸는데, 어떻게 움직일까?','roles':'어디로 갈까 → 지금 어떻게 움직일까','map':'새 정보가 이전 길을 막습니다','target':'앞쪽 지점은 지금 방향보다 왼쪽','equal_predict':'양쪽에 같은 속도를 요구하면?','equal':'같은 목표 → 대체로 전진','left_predict':'오른쪽이 더 빠르면?','left':'좌우 차이 → 몸의 방향 변화','spin_predict':'앞으로 + 뒤로, 함께 돌리면?','spin':'전진은 작고, 회전은 큽니다','compare':'세 관찰에서 두 성분 찾기','average':'전진 목표는 두 바퀴의 평균','fixed_mean':'평균은 그대로, 차이만 키우기','spacing':'나아간 거리의 차이가 각도를 만듭니다','rotation':'회전 목표는 차이 ÷ 간격','controller':'왼쪽 지점 → 왼쪽 회전 → 오른쪽 더 빠르게','response':'요구한 목표와 실제 응답은 다릅니다','stop':'0을 요구해도 즉시 정지하지 않습니다','feedback':'실제 상태를 읽어 다음 명령을 바꿉니다','avoid':'참고 경로와 실제 궤적 비교','limits':'교육용 계획·제어 + 물리 엔진','recap':'같은 평균에서 차이만 커지면?'}[kind]
    c.play(Transform(title,label(heading,37).move_to([0,3.25,0])),run_time=.5)
    if kind in ['question','roles']:
     g=VGroup(label('계획',38,P.result),Arrow(LEFT,RIGHT,color=P.fg),label('제어',38,P.sensor),Arrow(LEFT,RIGHT,color=P.fg),label('몸의 응답',38)).arrange(RIGHT,buff=.3).scale_to_fit_width(7).move_to([1.2,.5,0])
     swap(c,g);c.wait(sec*.3);c.play(Indicate(g[0] if kind=='question' else g[2]),run_time=1)
    elif kind in ['map','target','controller','feedback','avoid']:
     origin=np.array([-.8,-.1,0]);pts=D['plans'][1]['path'];route=line(pts,P.result).scale(.65).move_to([1.3,.3,0])
     drum=Circle(radius=.46,color='#D98150',fill_color='#D98150',fill_opacity=.25).move_to([1.3,.2,0]);forbid=Circle(radius=1.0,color=P.error,fill_color=P.error,fill_opacity=.06).move_to(drum)
     old=Line([-1.6,.2,0],[4.1,.2,0],color=P.muted)
     g=VGroup(old,drum)
     swap(c,g)
     if kind=='map':
      c.wait(sec*.22);c.play(GrowFromCenter(forbid),run_time=1);active.add(forbid)
      c.wait(sec*.2);c.play(Create(route),old.animate.set_opacity(.3),run_time=1.5);active.add(route)
     else:
      c.play(Create(route),run_time=.7);active.add(route)
      row=D['samples'][60];prev=D['samples'][59];o=W(prev['root_position_m']);t=W(row['lookahead_m'])
      # Same geometric transform as reference path, normalized to explanatory region.
      f=Arrow([1.8,-1,0],[1.8,.8,0],buff=0,color=P.sensor)
      target=Dot([-.1,.5,0],color=P.result);a=Arrow([1.8,-1,0],target.get_center(),buff=0,color=P.result)
      # The diagram is oriented, not an exact metric map. Sign verified from stored control input.
      error=(math.atan2(row['lookahead_m'][1]-prev['root_position_m'][1],row['lookahead_m'][0]-prev['root_position_m'][0])-prev['yaw_rad']+PI)%(2*PI)-PI
      assert error>0 and row['command_w_rad_s']>0
      if kind=='feedback':
       target.move_to([1.8-math.sin(error)*1.9,-1+math.cos(error)*1.9,0]);a=Arrow([1.8,-1,0],target.get_center(),buff=0,color=P.result)
      c.play(FadeOut(VGroup(old,drum,route)),GrowArrow(f),FadeIn(target),run_time=.7)
      target_name=label('앞쪽 지점',27,P.result).next_to(target,UP)
      if kind=='feedback':target_name.add_updater(lambda m:m.next_to(target,UP,buff=.18))
      active=VGroup(f,target,label('지금 방향',25,P.sensor).next_to(f,DOWN),target_name)
      note=label('방향 관계를 펼쳐 본 그림',23,P.muted).move_to([1.5,-2.55,0]);active.add(note);self.add(active)
      c.wait(sec*.2);c.play(GrowArrow(a),run_time=1);active.add(a)
      if kind in ['controller','feedback']:
       v,w=row['command_v_m_s'],row['command_w_rad_s'];b=D['config']['wheel_track_m'];goals(c,v-w*b/2,v+w*b/2)
       msg=label('방향 비교 → 다음 바퀴 목표',30).move_to([1.3,-2.15,0]);c.play(FadeIn(msg),run_time=.7);active.add(msg)
       if kind=='feedback':
        source=label('실험 2초의 상태 · 다음 목표 명령',25,P.muted).move_to([1.5,2.25,0]);c.play(FadeIn(source),run_time=.5);active.add(source)
        for idx in [90,120]:
         rr=D['samples'][idx];pp=D['samples'][idx-1]
         err=(math.atan2(rr['lookahead_m'][1]-pp['root_position_m'][1],rr['lookahead_m'][0]-pp['root_position_m'][0])-pp['yaw_rad']+PI)%(2*PI)-PI
         dest=np.array([1.8-math.sin(err)*1.9,-1+math.cos(err)*1.9,0])
         c.wait(sec*.06)
         c.play(target.animate.move_to(dest),Transform(a,Arrow([1.8,-1,0],dest,buff=0,color=P.result)),Transform(source,label(f'실험 {rr["t"]:.0f}초 · 방향 차이 {err:+.3f} rad',25,P.muted).move_to(source)),run_time=.8)
         goals(c,rr['command_v_m_s']-rr['command_w_rad_s']*b/2,rr['command_v_m_s']+rr['command_w_rad_s']*b/2)

    elif kind in ['equal_predict','equal','left_predict','left','spin_predict','spin']:
     key='equal' if kind.startswith('equal') else 'left' if kind.startswith('left') else 'spin'
     row=CASES[key]['samples'][30];goals(c,row['left_target_m_s'],row['right_target_m_s'])
     q=label('몸은 어떻게 움직일까요?' if kind.endswith('predict') else 'Blender 물리 응답으로 확인',35).move_to([1.5,.6,0]);swap(c,VGroup(q))
     if kind.endswith('predict'):
      c.wait(sec*.38);a=Arrow([.2,-.8,0],[.2,1.0,0],color=P.result) if key=='equal' else CurvedArrow([2,-.6,0],[.4,1,0],angle=PI/2,color=P.result)
      c.play(Create(a),run_time=1.5);active.add(a)
    elif kind=='compare':
     g=VGroup(*[VGroup(label(n,30),label(f'{CASES[k]["samples"][30]["left_target_m_s"]:+.2f} / {CASES[k]["samples"][30]["right_target_m_s"]:+.2f}',29,P.sensor),label(out,30,P.result)).arrange(DOWN,buff=.5) for k,n,out in [('equal','같은 속도','전진'),('left','오른쪽 더 빠름','전진 + 회전'),('spin','반대 방향','주로 회전')]]).arrange(RIGHT,buff=.45).scale_to_fit_width(7.8).move_to([1.5,.4,0]);swap(c,g)
     c.wait(sec*.3);c.play(Indicate(g[0]),run_time=1);c.play(Indicate(g[2]),run_time=1)
    elif kind in ['average','fixed_mean','rotation']:
     row=CASES['left']['samples'][30];l,r=row['left_target_m_s'],row['right_target_m_s'];goals(c,l,r)
     formula=label('전진 목표 = (왼쪽 + 오른쪽) ÷ 2' if kind!='rotation' else '회전 목표 = (오른쪽 − 왼쪽) ÷ 0.288m',32).scale_to_fit_width(7.9).move_to([1.6,1.0,0])
     swap(c,VGroup(formula));c.wait(sec*(.15 if kind=='fixed_mean' else .25))
     first,second=(l,r) if kind!='rotation' else (r,l)
     tail=f') ÷ 2 = {(l+r)/2:.2f} m/s' if kind!='rotation' else f') ÷ 0.288 = {(r-l)/.288:.3f} rad/s'
     equation=VGroup(label('(',34,P.result),label(f'{first:.2f}',34,P.fg if kind!='rotation' else P.sensor),label('+' if kind!='rotation' else '−',34,P.result),label(f'{second:.2f}',34,P.sensor if kind!='rotation' else P.fg),label(tail,34,P.result)).arrange(RIGHT,buff=.10).scale_to_fit_width(7.7).move_to([1.6,-.4,0])
     indices=[0,1] if kind!='rotation' else [1,0]
     sources=VGroup(*[label(f'{x:.2f}',30,P.fg if i==0 else P.sensor).move_to(values[i]) for i,x in zip(indices,[first,second])]);self.add(sources)
     c.play(sources[0].animate.move_to(equation[1]),sources[1].animate.move_to(equation[3]),run_time=1.5)
     c.play(FadeOut(sources),FadeIn(equation),run_time=.8);active.add(equation)
     if kind=='average':
      c.wait(sec*.10);goals(c,-.15,.15)
      c.play(Transform(equation,label('(-0.15 + 0.15) ÷ 2 = 0 m/s',34,P.result).move_to(equation)),run_time=.8)
      c.wait(sec*.10);goals(c,.2,.2)
      c.play(Transform(equation,label('(0.20 + 0.20) ÷ 2 = 0.20 m/s',34,P.result).move_to(equation)),run_time=.8)
     if kind=='fixed_mean':
      c.wait(sec*.12);goals(c,0,.3);changed=label('(0.00 + 0.30) ÷ 2 = 0.15 m/s',34,P.result).move_to(equation)
      c.play(Transform(equation,changed),run_time=.8);msg=label('평균 유지 · 차이 증가',29).move_to([1.6,-1.65,0]);c.play(FadeIn(msg),run_time=.7);active.add(msg)
     if kind=='rotation':
      note=label('미끄럼 없는 차동구동의 목표 변환',24,P.muted).move_to([1.6,-1.65,0]);c.play(FadeIn(note),run_time=.6);active.add(note)
      c.wait(sec*.15)
      wider=label('같은 차이 · 간격 2배 → 회전 목표 절반',27).scale_to_fit_width(7.5).move_to([1.6,-2.3,0]);c.play(FadeIn(wider),run_time=.65);active.add(wider)
    elif kind=='spacing':
     left=Line([-.2,-1,0],[-.2,.4,0],color=P.fg,stroke_width=7);right=Line([2.7,-1,0],[2.7,1.3,0],color=P.sensor,stroke_width=7);bridge=Line([-.2,-1,0],[2.7,-1,0],color=P.fg)
     g=VGroup(left,right,bridge,label('좌우 간격 b',29).next_to(bridge,DOWN),label('더 나아간 거리 Δs',28,P.sensor).move_to([2.8,2,0]));swap(c,g)
     c.wait(sec*.3);eq=label('돌아갈 각도 = 거리 차이 ÷ 바퀴 간격',30).scale_to_fit_width(7.7).move_to([1.5,-2.2,0]);c.play(FadeIn(eq),run_time=.8);active.add(eq)
    elif kind in ['response','stop']:
     goals(c,.2,.2)
     rows=CASES['stop']['samples'];ax=Axes(x_range=[0,6,1],y_range=[0,.25,.05],x_length=7.4,y_length=3.2,axis_config={'color':P.muted,'include_tip':False}).move_to([1.6,.2,0])
     target=ax.plot_line_graph([r['t'] for r in rows],[r['forward_target_m_s'] for r in rows],line_color=P.sensor,add_vertex_dots=False)
     actual=ax.plot_line_graph([r['t'] for r in rows],[math.hypot(*r['velocity_m_s'][:2]) for r in rows],line_color=P.result,add_vertex_dots=False)
     ticks=VGroup(*[label(str(x),21,P.muted).next_to(ax.c2p(x,0),DOWN,buff=.12) for x in [0,3,6]],*[label(f'{y:.2f}',20,P.muted).next_to(ax.c2p(0,y),LEFT,buff=.12) for y in [.1,.2]])
     g=VGroup(ax,ticks,label('시간 (s)',23,P.muted).move_to([4.7,-1.9,0]),label('전진 목표 / 몸의 속력 (m/s)',25).move_to([1.6,2.3,0]));swap(c,g)
     c.wait(sec*.2);c.play(Create(target),run_time=1);active.add(target)
     c.wait(sec*.2);c.play(Create(actual),run_time=2);active.add(actual)
     legend=VGroup(label('파랑: 요구한 전진 목표',25,P.sensor),label('초록: 계산된 몸의 속력',25,P.result)).arrange(DOWN,buff=.18).move_to([1.6,-2.25,0]);c.play(FadeIn(legend),run_time=.7);active.add(legend)
    elif kind=='limits':
     g=VGroup(label('교육용 계획·제어 모형',36),label('Bullet: 모터 · 관성 · 바닥 접촉',32,P.result),label('센서 / 실제 로봇 / Nav2 검증 아님',28,P.muted)).arrange(DOWN,buff=.6).move_to([1.5,.3,0]);swap(c,g)
    elif kind=='recap':
     goals(c,0,.3);g=VGroup(label('평균 유지 → 전진 목표 유지',34),label('좌우 차이 증가 → 회전 목표 증가',34,P.result),label('계획 → 명령 → 실제 응답',32)).arrange(DOWN,buff=.6).scale_to_fit_width(7.5).move_to([1.5,.3,0]);swap(c,g)

   if type(self).__name__=='FixedMeanPatch' and bid=='B13':return

class FixedMeanPatch(WheelDiscovery):
 """Execute preceding states without encoding; render the targeted beat only."""
 pass
