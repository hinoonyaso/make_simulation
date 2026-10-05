"""Discovery-first explanation. All map/path/pose states come from the existing V9 trace."""
import json
import sys
from pathlib import Path
import numpy as np
from manim import *

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'core/manim-robotics-education-skill/templates'))
from manim_kit import P,BeatClock,world_window,turtlebot3_top,named_section
DATA=json.loads((HERE/'../data/trace.json').read_text())
DOC=json.loads((HERE/'visual_manifest.json').read_text())
DUR={b['id']:b['sec'] for b in DOC['beats']}
SNAP=DATA['snapshots']
ALL_COSTS=np.asarray([s['cost'] for s in SNAP])
CRITICAL_IDS=tuple(DOC['critical_excerpt']['beat_ids'])
WBASE=world_window(12.)
def W(x,y):return WBASE(x,y)+np.array([-1.4,-.10,0.])
W.k=WBASE.k
DRUM='#E7773C'

def label(s,size=32,color=P.fg,width=None):
    obj=Text(s,font='NanumGothic',font_size=size,color=color)
    if width and obj.width>width:obj.scale_to_fit_width(width)
    return obj

def heading(s):return label(s,38,width=12.5).move_to([0,3.35,0])

def text_change(old,new):
    source=old.copy()
    def update(obj,alpha):
        obj.become(source if alpha<.5 else new)
        obj.set_opacity(1-2*alpha if alpha<.5 else 2*alpha-1)
    return UpdateFromAlphaFunc(old,update)

def panel(title,value,note=''):
    parts=[label(title,29,P.muted),label(value,56),label(note,26,P.muted)]
    g=VGroup(*parts).arrange(DOWN,buff=.23)
    if g.width>3.5:g.scale_to_fit_width(3.5)
    return g.move_to([4.7,.65,0])

def path_line(path,color,width=5):
    return VMobject(stroke_color=color,stroke_width=width,fill_opacity=0).set_points_as_corners([W(*p) for p in path])

def forbidden(path,snapshot):
    points=np.asarray(path)
    indices=np.round((points-[DATA['xs'][0],DATA['ys'][0]])/DATA['resolution_m']).astype(int)
    return np.asarray(snapshot['cost'])[indices[:,1],indices[:,0]]>=255

def costfield(snapshot):
    base=np.array(SNAP[0]['cost']);now=np.array(snapshot['cost']);g=VGroup()
    for j,y in enumerate(DATA['ys']):
        for i,x in enumerate(DATA['xs']):
            if abs(x)>3.4 or abs(y)>2.65:continue
            if not (base[j,i]>=255 or (ALL_COSTS[:,j,i].max()>=40 and ALL_COSTS[:,j,i].max()>base[j,i]+1)):continue
            v=now[j,i]
            if v>=255:
                dynamic=base[j,i]<255;color=P.error if dynamic else '#465162';opacity=.31 if dynamic else .18
            elif v>=40 and v>base[j,i]+1:color=P.active;opacity=.09
            else:color=P.error;opacity=0
            g.add(Square(side_length=DATA['resolution_m']*W.k,stroke_width=.3,stroke_opacity=1 if opacity else 0,stroke_color=color,fill_color=color,fill_opacity=opacity).move_to(W(x,y)))
    return g

def overlap_detail():
    """Magnify the exact recorded cells and vertices, rather than drawing a schematic collision."""
    center=np.array([4.7,.25,0.]);scale=3.0
    def local(x,y):return center+np.array([x*scale,(y+.75)*scale,0.])
    g=VGroup()
    costs=np.asarray(SNAP[2]['cost'])
    for j,y in enumerate(DATA['ys']):
        for i,x in enumerate(DATA['xs']):
            if abs(x)>.4501 or abs(y+.75)>.3001:continue
            bad=costs[j,i]>=255
            g.add(Square(side_length=DATA['resolution_m']*scale,stroke_width=.7,
                         stroke_color=P.error if bad else P.faint,fill_color=P.error,
                         fill_opacity=.28 if bad else 0).move_to(local(x,y)))
    points=[p for p in SNAP[1]['path'] if abs(p[0])<=.4501 and abs(p[1]+.75)<=.3001]
    g.add(VMobject(stroke_color=P.muted,stroke_width=4,fill_opacity=0).set_points_as_corners([local(*p) for p in points]))
    for p,bad in zip(SNAP[1]['path'],forbidden(SNAP[1]['path'],SNAP[2])):
        if bad:g.add(Dot(local(*p),radius=.10,color=P.error))
    g.add(label('겹친 부분 확대',26,P.muted,width=3.5).move_to([4.7,1.6,0]))
    g.add(label('금지 칸과 겹친 점 3개',27,P.error,width=3.5).move_to([4.7,-1.25,0]))
    return g

def anchor(beat,word):
    doc=json.loads((HERE/'assets/audio'/f'{beat}.alignment.json').read_text())
    words=[w for seg in doc['result']['segments'] for w in seg['words']]
    for w in words:
        matches=w['word'].strip()==word if word=='세' else word in w['word']
        if matches:return float(w['start'])
    raise ValueError(f'No measured anchor {beat}: {word}')

def until(clock,seconds):clock.wait(max(0.,seconds-clock.used))

class ObstacleDiscovery(MovingCameraScene):
    def setup_world(self):
        self.camera.background_color=P.bg
        self.det2=SNAP[1]['detected_xy'];self.det3=SNAP[2]['detected_xy']
        grid=VGroup(*[Line(W(x,-2.65),W(x,2.65),stroke_color=P.faint,stroke_width=.5,stroke_opacity=.25) for x in np.arange(-3.4,3.41,.3)],
                    *[Line(W(-3.4,y),W(3.4,y),stroke_color=P.faint,stroke_width=.5,stroke_opacity=.25) for y in np.arange(-2.4,2.41,.3)])
        boxes=VGroup(*[Rectangle(width=(x1-x0)*W.k,height=(y1-y0)*W.k,fill_color='#5B6574',fill_opacity=.8,stroke_color=P.muted,stroke_width=1).move_to(W((x0+x1)/2,(y0+y1)/2)) for x0,y0,x1,y1 in DATA['boxes']])
        self.drum=Circle(radius=DATA['circular_obstacle_radius_m']*W.k,stroke_color='#FFAE70',stroke_width=2,fill_color=DRUM,fill_opacity=1).move_to(W(*self.det2))
        goal=Circle(radius=.12*W.k,stroke_color=P.result,stroke_width=3).move_to(W(*DATA['goal'][:2]))
        goal_label=label('목표',26,P.muted).next_to(goal,DOWN,buff=.15)
        self.south=path_line(SNAP[1]['path'],P.result)
        self.field=costfield(SNAP[1])
        self.head=heading('같은 길인데, 왜 막힐까?')
        self.counter=panel('저장 경로의 금지 점','0개','2초 지도에서 확인')
        self.path_tag=label('2초에 저장한 경로',26,P.result).move_to(W(.1,-1.12))
        self.map_tag=label('장애물 정보 · 2초',25,P.muted,width=3.5).move_to([4.7,1.95,0])
        self.add(grid,boxes,goal,goal_label,self.drum,self.head)

    def critical(self):
        arrow=Arrow(W(*self.det2),W(*self.det3),buff=.04,color=P.active,stroke_width=3,max_tip_length_to_length_ratio=.20)
        named_section(self,'B04_predict')
        with BeatClock(self,DUR['B04']) as b:
            b.play(text_change(self.head,heading('길은 그대로. 정보가 내려오면?')),run_time=.7)
            until(b,anchor('B04','내려오면'))
            b.play(GrowArrow(arrow),run_time=.8)
        hits=[p for p,yes in zip(SNAP[1]['path'],forbidden(SNAP[1]['path'],SNAP[2])) if yes]
        assert len(hits)==3
        self.hits=VGroup(*[Dot(W(*p),radius=.075,color=P.error) for p in hits])
        hit_note=label('같은 경로의 3개 점',28,P.error).next_to(self.hits,DOWN,buff=.30)
        named_section(self,'B05_test_discover')
        with BeatClock(self,DUR['B05']) as b:
            b.play(text_change(self.head,heading('바뀐 지도에, 같은 길을 대입')),self.drum.animate.move_to(W(*self.det3)),Transform(self.field,costfield(SNAP[2])),text_change(self.map_tag,label('장애물 정보 · 3초',25,P.muted,width=3.5).move_to(self.map_tag)),FadeOut(arrow),FadeOut(self.path_tag),FadeOut(self.counter),run_time=1.6)
            until(b,anchor('B05','세'))
            self.counter=overlap_detail()
            b.play(self.south.animate.set_color(P.muted),LaggedStart(*[GrowFromCenter(x) for x in self.hits],lag_ratio=.15),FadeIn(hit_note),FadeIn(self.counter),run_time=1.)
        self.north=path_line(SNAP[2]['path'],P.result)
        self.north_tag=label('정기 갱신 · 3초 경로',25,P.result,width=3.5).move_to([4.7,-1.35,0])
        named_section(self,'B06_consequence')
        with BeatClock(self,DUR['B06']) as b:
            b.play(text_change(self.head,heading('새 경로는, 금지 칸을 피해 위로')),FadeOut(hit_note),run_time=.6)
            until(b,anchor('B06','위쪽'))
            b.play(self.south.animate.set_stroke(opacity=.18),self.hits.animate.set_opacity(.25),Create(self.north),FadeOut(self.counter),run_time=1.3)
            new_counter=panel('새 경로의 금지 점','0개','3초 지도에서 확인')
            b.play(FadeIn(new_counter),FadeIn(self.north_tag),run_time=.4)
            self.counter=new_counter

    def construct(self):
        self.setup_world()
        self.add(self.field,self.south,self.path_tag)
        named_section(self,'B01_question')
        with BeatClock(self,DUR['B01']) as b:
            until(b,anchor('B01','무엇'))
            b.play(self.drum.animate.move_to(W(*self.det3)),Transform(self.field,costfield(SNAP[2])),self.south.animate.set_color(P.muted),run_time=1.2)
        robot=turtlebot3_top(W,SNAP[1]['robot_xyyaw'])
        footprint=Circle(radius=DATA['robot_radius_m']*W.k,stroke_color=P.sensor,stroke_width=3).move_to(W(*SNAP[1]['robot_xyyaw'][:2]))
        ghost=DashedVMobject(Circle(radius=.25*W.k,stroke_color=P.sensor,stroke_width=3),num_dashes=28).move_to(W(self.det2[0]+.55,self.det2[1]))
        halo=Circle(radius=.77*W.k,stroke_color=P.error,stroke_width=2,fill_color=P.error,fill_opacity=.12).move_to(W(*self.det2))
        formula=VGroup(label('드럼 0.30 m',31),label('+ 로봇 0.25 m',31,P.sensor),label('+ 여유 0.22 m',31),label('= 금지 반경 0.77 m',31,P.active)).arrange(DOWN,aligned_edge=LEFT,buff=.24)
        formula.scale_to_fit_width(3.5).move_to([4.7,.55,0])
        named_section(self,'B02_geometry')
        with BeatClock(self,DUR['B02']) as b:
            b.play(text_change(self.head,heading('장애물만 피하면 충분할까?')),FadeOut(self.field),FadeOut(self.south),FadeOut(self.path_tag),self.drum.animate.move_to(W(*self.det2)),FadeIn(robot),run_time=.7)
            until(b,anchor('B02','크기'))
            b.play(Create(footprint),run_time=.7)
            until(b,anchor('B02','반지름'))
            b.play(TransformFromCopy(footprint,ghost),FadeIn(formula[:2]),run_time=.8)
            until(b,anchor('B02','여유'))
            b.play(ghost.animate.move_to(W(self.det2[0]+.77,self.det2[1])),GrowFromCenter(halo),FadeIn(formula[2:]),run_time=1.2)
        named_section(self,'B03_baseline')
        with BeatClock(self,DUR['B03']) as b:
            self.field=costfield(SNAP[1]);self.south=path_line(SNAP[1]['path'],P.result)
            b.play(text_change(self.head,heading('2초 지도: 이 길은 사용 가능')),FadeOut(formula),FadeOut(robot),FadeOut(footprint),FadeOut(ghost),FadeOut(halo),FadeIn(self.field),Create(self.south),FadeIn(self.path_tag),FadeIn(self.map_tag),run_time=1.2)
            until(b,anchor('B03','없습니다'))
            b.play(FadeIn(self.counter),run_time=.7)
        self.critical()
        rows=[r for r in DATA['playback'] if r['time']>=3.]
        rows.append({'time':DATA['metrics']['duration_s'],'pose':DATA['playback'][-1]['next_pose']})
        times=np.array([r['time'] for r in rows]);poses=np.array([r['pose'] for r in rows]);tau=ValueTracker(3.)
        def pose_at(t):
            i=int(np.clip(np.searchsorted(times,t,side='right')-1,0,len(times)-2))
            f=float(np.clip((t-times[i])/(times[i+1]-times[i]),0,1));xy=(1-f)*poses[i,:2]+f*poses[i+1,:2]
            turn=(poses[i+1,2]-poses[i,2]+np.pi)%(2*np.pi)-np.pi
            return [*xy,poses[i,2]+f*turn]
        def travelled():
            t=tau.get_value();indices=np.flatnonzero(times<=t)
            return path_line([*poses[indices,:2],pose_at(t)[:2]],P.sensor,3)
        live=always_redraw(lambda:turtlebot3_top(W,pose_at(tau.get_value())))
        trail=always_redraw(travelled)
        key=VGroup(label('초록: 기준 경로',27,P.result),label('파랑: 실제 위치',27,P.sensor)).arrange(DOWN,buff=.3).move_to([4.7,.5,0])
        named_section(self,'B07_playback')
        with BeatClock(self,DUR['B07']) as b:
            b.play(text_change(self.head,heading('경로와 실제 움직임은 다르다')),FadeOut(self.south),FadeOut(self.hits),FadeOut(self.counter),FadeOut(self.map_tag),FadeOut(self.north_tag),FadeIn(key),run_time=.7)
            self.add(trail,live)
            until(b,anchor('B07','초록색'))
            b.play(tau.animate.set_value(times[-1]),run_time=max(.5,DUR['B07']-b.used-.4),rate_func=linear)
        named_section(self,'B08_transfer_scope')
        transfer=label('겹치지 않는다면?\n계속 후보가 될 수 있다',29,width=3.5).move_to([4.7,.7,0])
        scope=label('교육용 모형\n실제 Nav2 DWB 실행 아님',27,P.muted,width=3.5).move_to([4.7,.65,0])
        with BeatClock(self,DUR['B08']) as b:
            b.play(text_change(self.head,heading('항상 바꾸기보다, 다시 확인하기')),FadeOut(key),FadeIn(transfer),self.north.animate.set_stroke(opacity=.55),run_time=.7)
            until(b,anchor('B08','교육용'))
            b.play(ReplacementTransform(transfer,scope),run_time=.6)

class CriticalInference(ObstacleDiscovery):
    def construct(self):
        self.setup_world()
        self.add(self.field,self.south,self.path_tag,self.map_tag,self.counter)
        self.critical()

class LayoutCheck(ObstacleDiscovery):
    """Silent layout probe, never evidence of narration or motion approval."""
    def construct(self):
        self.setup_world()
        self.drum.move_to(W(*self.det3))
        hits=[p for p,yes in zip(SNAP[1]['path'],forbidden(SNAP[1]['path'],SNAP[2])) if yes]
        self.head.become(heading('바뀐 지도에, 같은 길을 대입'))
        self.south.set_color(P.muted)
        self.add(costfield(SNAP[2]),self.south,
                 label('같은 경로의 3개 점',28,P.error).move_to(W(.0,-1.2)),
                 panel('이전 경로의 금지 점','3개','3초 지도에 대입'),
                 *[Dot(W(*p),radius=.075,color=P.error) for p in hits])
