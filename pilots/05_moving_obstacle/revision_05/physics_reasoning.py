"""Same Bullet run as Blender; then an explicit cut to a separate planning example."""
import json,sys
from pathlib import Path
import numpy as np
from manim import *
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'core/manim-robotics-education-skill/templates'))
from manim_kit import P,BeatClock,beat_seconds,apply_theme,txt
DOC=json.loads((HERE/'visual_manifest.json').read_text());BEATS={b['id']:b for b in DOC['beats']}
ROWS={c:json.loads((HERE/BEATS['P02'][key]).read_text())['samples'] for c,key in [('blocked','trace'),('clear','comparison_trace')]}

def label(s,size=32,color=P.fg):return txt(s,size=size,color=color)

def robot(row,level):
    body=Rectangle(width=.26*3,height=.22*3,stroke_color=P.fg,fill_color='#394455',fill_opacity=1).shift([-.064*3,0,0])
    wheels=VGroup(*[RoundedRectangle(width=.20,height=.11,corner_radius=.035,fill_color=P.fg,fill_opacity=1,stroke_width=0).shift([0,side*.144*3,0]) for side in [-1,1]])
    g=VGroup(body,wheels);g.rotate(row['yaw_rad']);g.shift([row['root_position_m'][0]*3+1.3,level+row['root_position_m'][1]*3,0]);return g

class PhysicalReasoning(Scene):
    def construct(self):
        apply_theme(self);seconds=beat_seconds(HERE/'visual_manifest.json','P02','P03')
        title=label('같은 바퀴 명령 → 다른 움직임',42).move_to([0,3.25,0])
        command=label('바퀴 모터의 목표 각속도는 동일',27,P.muted).move_to([0,2.65,0])
        note=label('물리 실험 · 단순 충돌 모형 · 회피 계획기 없음',24,P.muted).move_to([0,-3.15,0])
        clock=ValueTracker(0)
        levels={'clear':1.15,'blocked':-1.3};colors={'clear':P.sensor,'blocked':P.active}
        labels=VGroup();lanes=VGroup();bots={};paths={};numbers={}
        for case,level in levels.items():
            labels.add(label('장애물 없음' if case=='clear' else '드럼 있음',28,colors[case]).move_to([-4.6,level+.8,0]))
            lanes.add(Line([-2.25,level,0],[2.15,level,0],color=P.faint,stroke_width=3))
            def row_at(t,c=case):return ROWS[c][min(240,round(t*30))]
            bots[case]=always_redraw(lambda c=case,l=level:robot(ROWS[c][min(240,round(clock.get_value()*30))],l))
            def path(c=case,l=level):
                rows=ROWS[c][:max(2,min(241,round(clock.get_value()*30)+1))]
                return VMobject(stroke_color=colors[c],stroke_width=4).set_points_as_corners([[r['root_position_m'][0]*3+1.3,l+r['root_position_m'][1]*3,0] for r in rows])
            paths[case]=always_redraw(path)
            numbers[case]=always_redraw(lambda c=case,l=level:VGroup(DecimalNumber(ROWS[c][min(240,round(clock.get_value()*30))]['root_position_m'][0]-ROWS[c][0]['root_position_m'][0],num_decimal_places=2,font_size=46,color=colors[c]),label('m 전진',25,colors[c])).arrange(RIGHT,buff=.15).move_to([4.15,l,0]))
        drum=Circle(radius=.9,color='#E7773C',fill_color='#E7773C',fill_opacity=.65).move_to([1.3,-1.3,0])
        self.add(title,command,labels,lanes,drum,*paths.values(),*bots.values(),*numbers.values())
        with BeatClock(self,seconds[0]) as b:
            b.play(clock.animate.set_value(8),run_time=8.0,rate_func=linear)
        # Preserve the measured contact state, then distinguish the next model.
        frozen=VGroup(robot(ROWS['blocked'][-1],-1.3),drum.copy())
        for obj in [*bots.values(),*paths.values(),*numbers.values()]:obj.clear_updaters()
        with BeatClock(self,seconds[1]) as b:
            b.play(FadeOut(VGroup(labels,lanes,*bots.values(),*paths.values(),*numbers.values(),drum,command)),Transform(title,label('접촉 뒤의 반응과 접촉 전의 확인',40).move_to([0,3.25,0])),FadeIn(frozen),run_time=.7)
            # Fix Korean title before its display, no invented physics state.
            title.become(label('접촉 뒤의 반응과 접촉 전의 확인',40).move_to([0,3.25,0]))
            b.play(frozen.animate.move_to([-2.5,0,0]).scale(1.35),run_time=.8)
            response=label('물리 실험\n접촉 뒤 움직임이 달라짐',30,P.active).move_to([2.5,1.05,0])
            b.play(FadeIn(response),run_time=.6)
            b.wait(2.5)
            planning=label('지도에서 확인\n로봇 크기 + 여유를 고려',30,P.sensor).move_to([2.5,-.6,0])
            b.play(FadeIn(planning),run_time=.6)
            boundary=label('다음은 별도의 교육용 지도 모형',30,P.fg).move_to([0,-1.85,0])
            b.wait(4.5)
            b.play(FadeIn(boundary),run_time=.5)
