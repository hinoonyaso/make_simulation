"""One run: map update -> replanned reference -> feedback-driven physical position."""
import json,sys,math
from pathlib import Path
import numpy as np
from manim import *
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[2]/'core/manim-robotics-education-skill/templates'))
from manim_kit import P,BeatClock,beat_seconds,txt,apply_theme
DOC=json.loads((H/'visual_manifest.json').read_text());D=json.loads((H/'data/baseline_planner_on.json').read_text());ROWS=D['samples'];INITIAL=D['plans'][0]['path'];NEW=D['plans'][1]['path'];RADIUS=D['config']['drum_radius_m']+D['planner_config']['robot_radius_m']+D['planner_config']['margin_m']

def W(x,y):return np.array([x*2.8,y*2.8-.2,0.])
def label(s,size=31,color=P.fg):return txt(s,size=size,color=color)
def path(points,color,width=5):return VMobject(stroke_color=color,stroke_width=width,fill_opacity=0).set_points_as_corners([W(*p) for p in points])
def robot(row):
    r=Rectangle(width=.26*2.8,height=.22*2.8,fill_color='#394455',fill_opacity=1,stroke_color=P.fg).shift([-.064*2.8,0,0]);wh=VGroup(*[RoundedRectangle(width=.16,height=.10,corner_radius=.025,fill_opacity=1,color=P.fg).shift([0,s*.144*2.8,0]) for s in [-1,1]])
    return VGroup(r,wh).rotate(row['yaw_rad']).shift(W(*row['root_position_m'][:2]))

class ClosedLoopReasoning(Scene):
 def construct(self):
    apply_theme(self);dur=beat_seconds(H/'visual_manifest.json','B02','B03','B04')
    heading=label('실물과 지도 정보는 다릅니다',39).move_to([0,3.35,0])
    grid=VGroup(*[Line(W(x,-1.0),W(x,1.0),stroke_color=P.faint,stroke_width=.5,stroke_opacity=.3) for x in np.arange(-1.8,1.81,.1)],*[Line(W(-1.8,y),W(1.8,y),stroke_color=P.faint,stroke_width=.5,stroke_opacity=.3) for y in np.arange(-1.,1.01,.1)])
    drum=Circle(radius=.3*2.8,color='#D98150',fill_color='#D98150',fill_opacity=.35).move_to(W(0,0))
    old=path(INITIAL,P.muted);bot=robot(ROWS[0]);goal=Circle(radius=.15*2.8,color=P.result,stroke_width=3).move_to(W(1.3,0));goal_label=label('목표',25,P.result).next_to(goal,RIGHT,buff=.15)
    known=label('지도 정보 없음 · 드럼은 실제로 존재',25,P.muted).move_to([0,2.65,0])
    self.add(grid,drum,old,bot,goal,goal_label,heading,known)
    forbidden=Circle(radius=RADIUS*2.8,stroke_color=P.error,stroke_width=3,fill_color=P.error,fill_opacity=.09).move_to(W(0,0));radius_label=label('금지 반경\n0.77m',28,P.error).move_to([4.25,1.3,0])
    with BeatClock(self,dur[0]) as b:
      b.wait(4.1)
      b.play(Transform(known,label('지도 정보 추가 · 실험 2초',27,P.fg).move_to([0,2.65,0])),Transform(bot,robot(ROWS[60])),drum.animate.set_fill(opacity=.75),run_time=.6)
      b.wait(.8)
      b.play(GrowFromCenter(forbidden),FadeIn(radius_label),run_time=1.5)
    invalid=[p for p in INITIAL if math.hypot(*p)<RADIUS]
    invalid_line=path(invalid,P.error,8);new=path(NEW,P.result,5)
    with BeatClock(self,dur[1]) as b:
      b.play(Transform(heading,label('이전 길을 그대로 쓸 수 있을까?',38).move_to([0,3.35,0])),FadeOut(known),FadeIn(invalid_line),run_time=.6)
      b.wait(3.5)
      b.play(old.animate.set_opacity(.35),Create(new),run_time=2.9)
      b.wait(1.7)
      b.play(Transform(heading,label('새 경로는 물리 위치 명령이 아닙니다',37).move_to([0,3.35,0])),Indicate(bot,color=P.sensor,scale_factor=1.15),run_time=1.)
    clock=ValueTracker(2)
    bot.clear_updaters();bot.add_updater(lambda m:m.become(robot(ROWS[min(900,round(clock.get_value()*30))])))
    actual=always_redraw(lambda:path([r['root_position_m'][:2] for r in ROWS[:max(2,min(901,round(clock.get_value()*30)+1))]],P.sensor,5))
    flow=VGroup(*[label(s,25,P.sensor if i==0 else P.muted) for i,s in enumerate(['실제 위치','→ 바퀴 명령','→ 물리 반응','→ 다시 위치'])]).arrange(RIGHT,buff=.25).move_to([0,-2.75,0])
    self.add(actual)
    with BeatClock(self,dur[2]) as b:
      b.play(Transform(heading,label('계획과 실제 움직임을 연결하는 피드백',37).move_to([0,3.35,0])),FadeOut(radius_label),FadeOut(invalid_line),old.animate.set_opacity(.15),FadeIn(flow),run_time=.6)
      b.play(clock.animate.set_value(12),run_time=dur[2]-.8,rate_func=linear)
    bot.clear_updaters();actual.clear_updaters()
