"""One run: map update -> replanned reference -> feedback-driven physical position."""
import json, sys, math
from pathlib import Path
import numpy as np
from manim import *
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parents[2] / 'core/manim-robotics-education-skill/templates'))
from manim_kit import P, BeatClock, beat_seconds, txt, apply_theme
DOC = json.loads((H / 'visual_manifest.json').read_text())
D = json.loads((H / DOC['beats'][3]['trace']).read_text())
ROWS = D['samples']
INITIAL = D['plans'][0]['path']
NEW = D['plans'][1]['path']
RADIUS = D['config']['drum_radius_m'] + D['planner_config']['robot_radius_m'] + D['planner_config']['margin_m']

def W(x, y):
    return np.array([x * 2.8, y * 2.8 - 0.2, 0.0])

def label(s, size=31, color=P.fg):
    return txt(s, size=size, color=color)

def path(points, color, width=5):
    return VMobject(stroke_color=color, stroke_width=width, fill_opacity=0).set_points_as_corners([W(*p) for p in points])

def robot(row):
    r = Rectangle(width=0.26 * 2.8, height=0.22 * 2.8, fill_color='#394455', fill_opacity=1, stroke_color=P.fg).shift([-0.064 * 2.8, 0, 0])
    wh = VGroup(*[RoundedRectangle(width=0.16, height=0.1, corner_radius=0.025, fill_opacity=1, color=P.fg).shift([0, s * 0.144 * 2.8, 0]) for s in [-1, 1]])
    return VGroup(r, wh).rotate(row['yaw_rad']).shift(W(*row['root_position_m'][:2]))

def change_sentence(old, new):
    """Local text replacement; geometry remains visible and callers retain new."""
    return Succession(FadeOut(old), FadeIn(new))

class ClosedLoopReasoning(Scene):

    def construct(self):
        apply_theme(self)
        dur = beat_seconds(H / 'visual_manifest.json', 'B02', 'B03', 'B04')
        central={r['id']:r['sec'] for r in DOC['beats'] if r['id'].startswith('B04')}
        heading = label('실물과 지도 정보는 다릅니다', 39).move_to([0, 3.35, 0])
        grid = VGroup(*[Line(W(x, -1.0), W(x, 1.0), stroke_color=P.faint, stroke_width=0.5, stroke_opacity=0.3) for x in np.arange(-1.8, 1.81, 0.1)], *[Line(W(-1.8, y), W(1.8, y), stroke_color=P.faint, stroke_width=0.5, stroke_opacity=0.3) for y in np.arange(-1.0, 1.01, 0.1)])
        drum = Circle(radius=0.3 * 2.8, color='#D98150', fill_color='#D98150', fill_opacity=0.35).move_to(W(0, 0))
        old = path(INITIAL, P.muted)
        bot = robot(ROWS[0])
        goal = Circle(radius=0.15 * 2.8, color=P.result, stroke_width=3).move_to(W(1.3, 0))
        goal_label = label('목표', 25, P.result).next_to(goal, RIGHT, buff=0.15)
        known = label('지도 정보 없음 · 드럼은 실제로 존재', 25, P.muted).move_to([0, 2.65, 0])
        self.add(grid, drum, old, bot, goal, goal_label, heading, known)
        forbidden = Circle(radius=RADIUS * 2.8, stroke_color=P.error, stroke_width=3, fill_color=P.error, fill_opacity=0.09).move_to(W(0, 0))
        radius_label = label('금지 반경\n0.77m', 28, P.error).move_to([4.25, 1.3, 0])
        with BeatClock(self, dur[0]) as b:
            b.wait(4.1)
            known_next = label('지도 정보 추가 · 실험 2초', 27, P.fg).move_to([0, 2.65, 0])
            b.play(change_sentence(known, known_next), Transform(bot, robot(ROWS[60])), drum.animate.set_fill(opacity=0.75), run_time=0.6)
            known = known_next
            b.wait(0.8)
            b.play(GrowFromCenter(forbidden), FadeIn(radius_label), run_time=1.5)
        invalid = [p for p in INITIAL if math.hypot(*p) < RADIUS]
        invalid_line = path(invalid, P.error, 8)
        new = path(NEW, P.result, 5)
        with BeatClock(self, dur[1]) as b:
            heading_next = label('이전 길을 그대로 쓸 수 있을까?', 38).move_to([0, 3.35, 0])
            b.play(change_sentence(heading, heading_next), FadeOut(known), FadeIn(invalid_line), run_time=0.6)
            heading = heading_next
            b.wait(dur[1]*.26)
            b.play(old.animate.set_opacity(0.35), Create(new), run_time=2.2)
            b.wait(.4)
            heading_next = label('길은 정했는데, 어떻게 움직일까?', 37).move_to([0, 3.35, 0])
            b.play(change_sentence(heading, heading_next), Indicate(bot, color=P.sensor, scale_factor=1.15), run_time=1.0)
            heading = heading_next
        row,prev=ROWS[60],ROWS[59]
        cfg=D['config'];v=row['command_v_m_s'];omega=row['command_w_rad_s'];track=cfg['wheel_track_m']
        right,left=v+omega*track/2,v-omega*track/2
        assert right>left and abs((right-left)/track-omega)<1e-9
        origin=W(*prev['root_position_m'][:2]);target=W(*row['lookahead_m'])
        heading_vec=np.array([math.cos(prev['yaw_rad']),math.sin(prev['yaw_rad']),0])
        target_angle=math.atan2(target[1]-origin[1],target[0]-origin[0])
        error=(target_angle-prev['yaw_rad']+PI)%(2*PI)-PI
        assert error>0 and omega>0
        forward=Arrow(origin,origin+1.4*heading_vec,buff=0,color=P.sensor)
        direction=Arrow(origin,target,buff=0,color=P.result)
        target_dot=Dot(target,color=P.result,radius=.065)
        target_name=label('새 길의 앞쪽 지점',26,P.result).next_to(target_dot,UP,buff=.18)
        current_name=label('지금 방향',24,P.sensor).next_to(forward,DOWN,buff=.15)
        angle=Arc(radius=.72,start_angle=prev['yaw_rad'],angle=error,color=P.fg,stroke_width=5).shift(origin)
        causal=label('지금 방향보다 왼쪽 → 왼쪽 회전 명령',30).move_to([0,-2.5,0])
        with BeatClock(self,central['B04']) as b:
            heading_next=label('제어기는 앞쪽 지점을 향하게 합니다',37).move_to([0,3.35,0])
            b.play(change_sentence(heading,heading_next),FadeOut(radius_label),FadeOut(invalid_line),GrowArrow(forward),GrowArrow(direction),FadeIn(target_dot),FadeIn(target_name),FadeIn(current_name),run_time=.8)
            heading=heading_next
            b.wait(max(0,central['B04']*.47-.8))
            b.play(Create(angle),FadeIn(causal),run_time=.7)
        # Keep the selected-target geometry as a context inset at the same source time.
        context=VGroup(new.copy(),robot(prev),forward.copy(),direction.copy(),target_dot.copy()).scale_to_fit_width(3.0).move_to([-3.6,.6,0])
        context_name=label('앞쪽 지점은 왼쪽',25,P.result).move_to([-3.6,-1.15,0])
        body=RoundedRectangle(width=1.4,height=1.8,corner_radius=.12,color=P.fg,fill_color='#394455',fill_opacity=1).move_to([1.9,-.05,0])
        wheels=VGroup(*[RoundedRectangle(width=.25,height=.65,corner_radius=.05,color=P.fg,fill_opacity=1).move_to([x,-.05,0]) for x in [1.05,2.75]])
        arrows=VGroup(*[Arrow([x,.3,0],[x,.3+speed*4.5,0],buff=0,color=P.sensor,stroke_width=7,max_tip_length_to_length_ratio=.18) for x,speed in [(1.05,left),(2.75,right)]])
        left_value=label(f'{left:.3f}',29);right_value=label(f'{right:.3f}',29,P.sensor)
        left_label=VGroup(label('왼쪽',27),VGroup(left_value,label('m/s',23)).arrange(RIGHT,buff=.10)).arrange(DOWN,buff=.08).move_to([.45,-1.2,0])
        right_label=VGroup(label('오른쪽',27,P.sensor),VGroup(right_value,label('m/s',23,P.sensor)).arrange(RIGHT,buff=.10)).arrange(DOWN,buff=.08).move_to([3.6,-1.2,0])
        title=label('목표 = 바퀴에 요구하는 속도',36).move_to([0,3.3,0])
        note=label('실험 2초 명령 · 위쪽이 앞',24,P.muted).move_to([0,2.65,0])
        definition=label('실제로 측정한 속도와 구분',29).move_to([0,-2.2,0])
        turn=CurvedArrow([2.3,1.7,0],[1.2,1.5,0],angle=PI/3,color=P.result)
        with BeatClock(self,central['B04D']) as b:
            b.play(FadeOut(VGroup(grid,drum,old,new,bot,goal,goal_label,forbidden,forward,direction,target_dot,target_name,current_name,angle,causal,heading)),run_time=.35)
            b.play(FadeIn(context),FadeIn(context_name),FadeIn(title),FadeIn(note),FadeIn(body),FadeIn(wheels),FadeIn(definition),run_time=.65)
        rule=label('오른쪽을 더 빠르게 → 왼쪽 회전',30).move_to([0,-2.2,0])
        with BeatClock(self,central['B04W']) as b:
            b.play(FadeOut(definition),GrowArrow(arrows[0]),GrowArrow(arrows[1]),FadeIn(left_label),FadeIn(right_label),Create(turn),FadeIn(rule),run_time=1.0)
        # Final assembly replaces this measured beat with the validated recorded component replay.
        with BeatClock(self,central['B04P']) as b:
            b.wait(central['B04P'])
        avg=VGroup(*[label(t,26,P.sensor if i==4 else P.result if i==6 else P.fg) for i,t in enumerate(['전진 목표 =','(',f'{left:.3f}','+',f'{right:.3f}',') ÷ 2 =',f'{v:.3f}','m/s'])]).arrange(RIGHT,buff=.085).move_to([0,-2.2,0])
        rot=VGroup(*[label(t,26,P.sensor if i==2 else P.result if i==9 else P.fg) for i,t in enumerate(['회전 목표 =','(',f'{right:.3f}','−',f'{left:.3f}',') ÷',f'{track:.3f}','m','=',f'{omega:.1f}','rad/s'])]).arrange(RIGHT,buff=.085).move_to([0,-2.2,0])
        avg_ops=VGroup(*[avg[i] for i in [0,1,3,5,7]]);rot_ops=VGroup(*[rot[i] for i in [0,1,3,5,7,8,10]])
        spacing=DoubleArrow([1.05,-.38,0],[2.75,-.38,0],buff=0,color=P.muted,stroke_width=2)
        track_value=label(f'{track:.3f}',22)
        track_label=VGroup(track_value,label('m',22)).arrange(RIGHT,buff=.07).move_to([1.9,-.65,0])
        with BeatClock(self,central['B04A']) as b:
            b.play(FadeOut(rule),FadeIn(avg_ops),run_time=.4)
            b.play(TransformFromCopy(left_value,avg[2],path_arc=.25),run_time=.65)
            b.play(TransformFromCopy(right_value,avg[4],path_arc=-.25),run_time=.65)
            b.play(FadeIn(avg[6]),run_time=.3)
            self.remove(avg_ops,*avg.submobjects);self.add(avg)
        with BeatClock(self,central['B04R']) as b:
            b.play(FadeOut(avg),Create(spacing),FadeIn(track_label),run_time=.4)
            b.play(FadeIn(rot_ops),run_time=.3)
            b.play(TransformFromCopy(right_value,rot[2],path_arc=-.25),run_time=.65)
            b.play(TransformFromCopy(left_value,rot[4],path_arc=.25),run_time=.65)
            b.play(TransformFromCopy(track_value,rot[6],path_arc=.25),run_time=.65)
            b.play(FadeIn(rot[9]),run_time=.3)
            self.remove(rot_ops,*rot.submobjects);self.add(rot)
        with BeatClock(self,central['B04X']) as b:
            avg.move_to([0,-2.05,0]);rot.generate_target();rot.target.move_to([0,-2.65,0])
            b.play(MoveToTarget(rot),FadeIn(avg),run_time=.4)
            equal=VGroup(*[Arrow([x,.3,0],[x,.3+v*4.5,0],buff=0,color=P.sensor,stroke_width=7) for x in [1.05,2.75]])
            equal_note=label('가정: 전진 목표는 유지 · 양쪽 목표를 같게',25,P.muted).move_to([0,2.65,0])
            b.play(Transform(arrows,equal),FadeOut(turn),change_sentence(note,equal_note),Transform(left_value,label(f'{v:.3f}',29).move_to(left_value)),Transform(right_value,label(f'{v:.3f}',29,P.sensor).move_to(right_value)),*[Transform(token,label(f'{v:.3f}',26,color).move_to(token)) for token,color in [(avg[2],P.fg),(avg[4],P.sensor),(rot[2],P.sensor),(rot[4],P.fg)]],Transform(rot[9],label('0.0',26,P.result).move_to(rot[9])),run_time=.85)
        with BeatClock(self,central['B04E']) as b:
            # Keep the referenced numbers visible through '이 숫자는 명령입니다'.
            b.wait(1.8)
            b.play(FadeOut(avg),FadeOut(rot),FadeOut(left_label),FadeOut(right_label),FadeOut(track_label),FadeOut(spacing),change_sentence(equal_note,label('같은 실행의 실제 움직임 확인',25,P.muted).move_to([0,2.65,0])),run_time=.4)
            b.play(FadeIn(label('요구한 명령 → 다음 컷의 기록된 응답',29).move_to([0,-2.2,0])),Transform(arrows,VGroup(*[Arrow([x,.3,0],[x,.3+speed*4.5,0],buff=0,color=P.sensor,stroke_width=7,max_tip_length_to_length_ratio=.18) for x,speed in [(1.05,left),(2.75,right)]])),run_time=.6)
