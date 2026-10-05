"""Persistent, synchronized map reasoning from the pilot V9 trace. No new planner execution."""
import json
import sys
from pathlib import Path
import numpy as np
from manim import *

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'core/manim-robotics-education-skill/templates'))
from manim_kit import P, BeatClock, world_window, turtlebot3_top, named_section, data_polyline
DATA=json.loads((HERE/'../data/trace.json').read_text())
DOC=json.loads((HERE/'visual_manifest.json').read_text())
DUR={b['id']:b['sec'] for b in DOC['beats']}
SNAP=DATA['snapshots']
W0=world_window(12.0)
def W(x,y): return W0(x,y)+np.array([-1.4,-.10,0.])
W.k=W0.k
DRUM='#E7773C'
FONT='NanumGothic'

def text(s,size=34,color=P.fg):
    return Text(s,font=FONT,font_size=size,color=color)

def blocked(path,snap):
    pts=np.array(path)
    ij=np.round((pts-[DATA['xs'][0],DATA['ys'][0]])/DATA['resolution_m']).astype(int)
    return np.array(snap['cost'])[ij[:,1],ij[:,0]]>=255

def route(path,color,width=5,dashed=False):
    line=VMobject(stroke_color=color,stroke_width=width,fill_opacity=0).set_points_as_corners([W(*p) for p in path])
    return DashedVMobject(line,num_dashes=42) if dashed else line

def field(snap):
    base=np.array(SNAP[0]['cost']); cur=np.array(snap['cost']); g=VGroup()
    for j,y in enumerate(DATA['ys']):
        for i,x in enumerate(DATA['xs']):
            if abs(x)>3.4 or abs(y)>2.65: continue
            val=cur[j,i]
            if val>=255:
                dynamic=base[j,i]<255
                col=P.error if dynamic else '#465162'
                op=.35 if dynamic else .20
            elif val>=40 and val>base[j,i]+1:
                col=P.active;op=.10
            else: continue
            g.add(Square(side_length=DATA['resolution_m']*W.k,stroke_width=.25,
                         stroke_color=col,fill_color=col,fill_opacity=op).move_to(W(x,y)))
    return g

def info(title,value,note=''):
    items=[text(title,30,P.muted),text(value,58,P.fg)]
    if note: items.append(text(note,27,P.muted))
    g=VGroup(*items).arrange(DOWN,buff=.22).move_to([4.7,.85,0])
    if g.width>3.4:g.scale_to_fit_width(3.4)
    return g

class MovingObstacleReasoning(MovingCameraScene):
    def construct(self):
        self.camera.background_color=P.bg
        grid=VGroup(*[Line(W(x,-2.65),W(x,2.65),stroke_color=P.faint,stroke_width=.5,stroke_opacity=.32)
                       for x in np.arange(-3.4,3.41,.3)],
                    *[Line(W(-3.4,y),W(3.4,y),stroke_color=P.faint,stroke_width=.5,stroke_opacity=.32)
                       for y in np.arange(-2.4,2.41,.3)])
        boxes=VGroup(*[Rectangle(width=(x1-x0)*W.k,height=(y1-y0)*W.k,fill_color='#5B6574',
                         fill_opacity=.85,stroke_width=1,stroke_color=P.muted).move_to(W((x0+x1)/2,(y0+y1)/2))
                         for x0,y0,x1,y1 in DATA['boxes']])
        header=text('드럼만 피하면 될까?',40).move_to([0,3.40,0])
        det2=SNAP[1]['detected_xy'];det3=SNAP[2]['detected_xy']
        drum=Circle(radius=DATA['circular_obstacle_radius_m']*W.k,fill_color=DRUM,
                    fill_opacity=1,stroke_color='#FFAE70',stroke_width=2).move_to(W(*det2))
        robot=turtlebot3_top(W,SNAP[1]['robot_xyyaw'])
        footprint=Circle(radius=DATA['robot_radius_m']*W.k,stroke_color=P.sensor,stroke_width=3).move_to(W(*SNAP[1]['robot_xyyaw'][:2]))
        goal=Circle(radius=.12*W.k,stroke_color=P.result,stroke_width=3).move_to(W(*DATA['goal'][:2]))
        goal_tag=text('목표',27,P.muted).next_to(goal,DOWN,buff=.15)
        old=route(SNAP[0]['path'],P.sensor,4,dashed=True)
        dims=VGroup(text('드럼   0.30 m',33),text('+ 로봇   0.25 m',33),text('+ 여유   0.22 m',33),text('= 금지 반경  0.77 m',33,P.active)).arrange(DOWN,aligned_edge=LEFT,buff=.32).move_to([4.6,.8,0])
        radius=.3+.25+.22
        halo=Circle(radius=radius*W.k,stroke_color=P.error,stroke_width=2,
                    fill_color=P.error,fill_opacity=.12).move_to(W(*det2))
        # The radius is the source model's planning threshold, not a Nav2 default.
        radius_mark=Line(W(*det2),W(det2[0]+radius,det2[1]),color=P.active,stroke_width=4)
        size_ghost=DashedVMobject(Circle(radius=.25*W.k,stroke_color=P.sensor,stroke_width=3),num_dashes=24).move_to(W(det2[0]+.55,det2[1]))
        self.add(grid,boxes,goal,goal_tag,old,drum,robot,header)
        named_section(self,'footprint')
        with BeatClock(self,DUR['B02']) as b:
            b.play(Create(footprint),FadeIn(dims[:2]),run_time=1.5)
            b.play(TransformFromCopy(footprint,size_ghost),run_time=1.0)
            b.wait(DUR['B02']*.30-2.5)
            b.play(FadeIn(dims[2]),GrowFromCenter(halo),Create(radius_mark),size_ghost.animate.move_to(W(det2[0]+.77,det2[1])),run_time=2.0)
            b.play(FadeIn(dims[3]),run_time=1.0)
        # Exact grid nodes, not a conservative four-corner maximum overlay.
        cost=field(SNAP[1]);markers=VGroup(*[Dot(W(*p),radius=.055,color=P.error) for p,yes in zip(SNAP[0]['path'],blocked(SNAP[0]['path'],SNAP[1])) if yes])
        panel=info('직선 경로의 금지 점','9개')
        header2=text('2초 지도: 원래 길은 막힌다',44).move_to(header)
        named_section(self,'old_path_blocked')
        with BeatClock(self,DUR['B03']) as b:
            b.play(Transform(header,header2),FadeOut(dims),FadeOut(radius_mark),FadeOut(footprint),FadeOut(size_ghost),FadeOut(halo),FadeIn(cost),run_time=1.0)
            b.wait(1.5)
            b.play(old.animate.set_color(P.error),LaggedStart(*[GrowFromCenter(m) for m in markers],lag_ratio=.1),FadeIn(panel),run_time=2.0)
        south=route(SNAP[1]['path'],P.result)
        south_tag=text('저장 경로 · t = 2s',28,P.result).move_to(W(.1,-1.13))
        named_section(self,'south_plan')
        with BeatClock(self,DUR['B04']) as b:
            b.play(Transform(header,text('2초 지도: 금지 칸을 피해 우회',44).move_to(header)),old.animate.set_stroke(opacity=.20),markers.animate.set_opacity(.20),Create(south),FadeIn(south_tag),Transform(panel,info('첫 경로의 금지 점','0개','2초 지도 기준')),run_time=2.3)
        cost3=field(SNAP[2])
        blocked3=blocked(SNAP[1]['path'],SNAP[2])
        hit3=VGroup(*[Dot(W(*p),radius=.07,color=P.error) for p,yes in zip(SNAP[1]['path'],blocked3) if yes])
        hit_label=text('새 금지 칸과 겹침',29,P.error).next_to(hit3,DOWN,buff=.24)
        ghost=drum.copy().set_opacity(.20)
        arrow=Arrow(W(*det2),W(*det3),buff=.03,color=P.active,stroke_width=3,max_tip_length_to_length_ratio=.2)
        named_section(self,'map_change')
        with BeatClock(self,DUR['B05']) as b:
            b.play(Transform(header,text('3초 지도: 같은 길을 다시 확인',44).move_to(header)),FadeOut(old),FadeOut(markers),FadeOut(south_tag),run_time=.8)
            self.add(ghost)
            b.play(drum.animate.move_to(W(*det3)),Transform(cost,cost3),Transform(robot,turtlebot3_top(W,SNAP[2]['robot_xyyaw'])),GrowArrow(arrow),run_time=2.5)
            b.wait(1.0)
            b.play(south.animate.set_color(P.muted),LaggedStart(*[GrowFromCenter(m) for m in hit3],lag_ratio=.2),FadeIn(hit_label),Transform(panel,info('이전 경로의 금지 점','3개','3초 지도에 대입')),run_time=1.6)
        north=route(SNAP[2]['path'],P.result)
        north_tag=text('정기 갱신 · t = 3s',27,P.result).move_to([4.7,-1.4,0])
        named_section(self,'north_plan')
        with BeatClock(self,DUR['B06']) as b:
            b.play(Transform(header,text('3초 지도: 새 경로를 확인',44).move_to(header)),south.animate.set_stroke(opacity=.2),hit3.animate.set_opacity(.3),FadeOut(hit_label),FadeOut(arrow),FadeOut(ghost),
                   Create(north),FadeIn(north_tag),Transform(panel,info('새 경로의 금지 점','0개','3초 지도 기준')),run_time=2.5)
        # Playback starts only after reasoning. Full recorded pose order is retained.
        rows=[row for row in DATA['playback'] if row['time']>=3.0]
        rows.append({'time':DATA['metrics']['duration_s'],'pose':DATA['playback'][-1]['next_pose']})
        tau=ValueTracker(3.0)
        times=np.array([row['time'] for row in rows]);poses=np.array([row['pose'] for row in rows])
        def pose_at(t):
            idx=min(np.searchsorted(times,t,side='right')-1,len(times)-2);idx=max(0,idx)
            f=np.clip((t-times[idx])/(times[idx+1]-times[idx]),0,1)
            xy=(1-f)*poses[idx,:2]+f*poses[idx+1,:2]
            dyaw=(poses[idx+1,2]-poses[idx,2]+np.pi)%(2*np.pi)-np.pi
            return [*xy,poses[idx,2]+f*dyaw]
        robot_live=always_redraw(lambda:turtlebot3_top(W,pose_at(tau.get_value())))
        actual=route([row['pose'][:2] for row in rows],P.sensor,2)
        actual.set_stroke(opacity=.6)
        named_section(self,'execute')
        with BeatClock(self,DUR['B07']) as b:
            b.play(FadeOut(south),FadeOut(hit3),FadeOut(panel),Transform(header,text('비교를 마친 뒤, 로봇 위치 기록 재생',44).move_to(header)),run_time=.6)
            self.remove(robot);self.add(robot_live)
            b.play(Create(actual),tau.animate.set_value(times[-1]),run_time=max(1.,DUR['B07']-1.2),rate_func=linear)
        named_section(self,'recap')
        with BeatClock(self,DUR['B08']) as b:
            b.play(Transform(header,text('정보가 바뀌면, 길의 조건도 바뀐다',44).move_to(header)),north.animate.set_stroke(opacity=.4),FadeOut(north_tag),run_time=1.)
            boundary=text('교육용 모형\n실제 Nav2 DWB 실행 아님',30,P.muted)
            boundary.scale_to_fit_width(3.5).move_to([4.7,.85,0]);self.add(boundary)
