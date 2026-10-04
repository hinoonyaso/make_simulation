"""One-file Manim lesson. Run after prepare_audio.py tts; see PRODUCTION.md."""
from pathlib import Path
import json
import math
import os
import numpy as np
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.base import SpeechService

ROOT = Path(__file__).resolve().parent
BG = "#F7F9FC"
INK = "#202D43"
MUTED = "#65738A"
BLUE = "#2175D9"
PURPLE = "#8556C8"
ORANGE = "#ED931D"
GREEN = "#1B9270"
RED = "#D54D53"
GRID = "#DFE6EF"
FONT = "NanumGothic"
L1, L2 = 1.0, 0.8


def label(text, size=27, color=INK, **kwargs):
    return Text(text, font=FONT, font_size=size, color=color, **kwargs)


def equation(tex, size=35, width=5.65):
    m = MathTex(tex, font_size=size, color=INK)
    if m.width > width:
        m.scale_to_fit_width(width)
    return m


def fk(a, b):
    return np.array([L1*np.cos(a)+L2*np.cos(a+b), L1*np.sin(a)+L2*np.sin(a+b)])


def ik(x, y, branch=1):
    d = (x*x+y*y-L1*L1-L2*L2)/(2*L1*L2)
    if abs(d) > 1 + 1e-10:
        raise ValueError("Target outside the ideal position workspace")
    d = np.clip(d, -1, 1)
    b = np.arctan2(branch*np.sqrt(max(0, 1-d*d)), d)
    a = np.arctan2(y, x)-np.arctan2(L2*np.sin(b), L1+L2*np.cos(b))
    return np.array([a, b])


def jacobian(a, b):
    return np.array([[-L1*np.sin(a)-L2*np.sin(a+b), -L2*np.sin(a+b)],
                     [L1*np.cos(a)+L2*np.cos(a+b), L2*np.cos(a+b)]])


class PreparedSpeech(SpeechService):
    """Local, frame-aligned WAV files are the source of truth for scene duration."""
    def __init__(self, records):
        super().__init__(cache_dir=str(ROOT / "assets/audio"))
        self.lookup = {r["text"]: r for r in records}

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        rec = self.lookup[text]
        return {"input_text":text, "input_data":{"input_text":text, "service":"prepared-edge-tts"},
                "original_audio":Path(rec["audio"]).name}


class ManipulatorLesson(VoiceoverScene):
    def construct(self):
        self.camera.background_color = BG
        self.doc = json.loads((ROOT / "storyboard.json").read_text())
        self.records = json.loads((ROOT / "assets/audio/manifest.json").read_text())
        self.set_speech_service(PreparedSpeech(self.records), create_subcaption=False)
        self.actual_timeline = []
        selected = os.environ.get("LESSON_CHAPTER")
        for ci, chapter in enumerate(self.doc["chapters"]):
            if selected and chapter["id"] != selected:
                continue
            self.ci = ci
            self.clear()
            self.header(chapter["title"], ci)
            getattr(self, "chapter_"+chapter["id"])()
        path = ROOT / "output" / ("preview_timeline.json" if selected else "render_timeline.json")
        path.write_text(json.dumps(self.actual_timeline, ensure_ascii=False, indent=2))

    def header(self, title, ci):
        brand = label("ROBOTICS / KINEMATICS", 16, BLUE).to_corner(UL, buff=.42)
        title_m = label(title, 34).move_to([-0.2, 2.98, 0])
        title_m.align_to(brand, LEFT)
        rule = Line([-6.65, 2.52, 0], [6.65, 2.52, 0], color=GRID, stroke_width=2)
        page = label(f"{ci+1:02d} / 12", 19, MUTED).to_corner(UR, buff=.42)
        foot = label("평면 2R 기구학 · 교육용 예시 (illustrative)", 16, MUTED).move_to([0, -2.88, 0])
        track = Line([-7.1,-3.95,0], [7.1,-3.95,0], color=GRID, stroke_width=6)
        fill = Line([-7.1,-3.95,0], [-7.1+14.2*(ci+1)/12,-3.95,0], color=BLUE, stroke_width=6)
        self.add(brand, title_m, rule, page, foot, track, fill)

    def rig(self, a=30*DEGREES, b=60*DEGREES):
        self.axes = Axes(x_range=[-2,2,.5], y_range=[-2,2,.5], x_length=5.0, y_length=5.0,
            tips=False, axis_config={"color":GRID, "stroke_width":2, "include_ticks":True,
                                    "tick_size":.035}).move_to([-3.85, -.12, 0])
        self.q1, self.q2 = ValueTracker(a), ValueTracker(b)
        self.add(self.axes)
        self.add(label("x [m]", 18, MUTED).next_to(self.axes.x_axis.get_end(), UP, buff=.08),
                 label("y [m]", 18, MUTED).next_to(self.axes.y_axis.get_end(), RIGHT, buff=.08),
                 label("0", 17, MUTED).next_to(self.axes.c2p(0,0), DL, buff=.08))
        self.arm = always_redraw(lambda:self.robot(self.q1.get_value(), self.q2.get_value()))
        self.add(self.arm)
        panel = RoundedRectangle(width=6.15, height=4.85, corner_radius=.18,
            stroke_color=GRID, stroke_width=1, fill_color=WHITE, fill_opacity=1).move_to([3.22,-.04,0])
        self.add(panel)

    def robot(self, a, b, opacity=1):
        o = self.axes.c2p(0,0)
        e = self.axes.c2p(L1*np.cos(a),L1*np.sin(a))
        p = self.axes.c2p(*fk(a,b))
        g = VGroup(Line(o,e, color=BLUE, stroke_width=17),
                   Line(e,p, color=PURPLE, stroke_width=15),
                   Dot(o,.125,color=INK), Dot(e,.115,color=INK), Dot(p,.095,color=ORANGE),
                   Dot(o,.045,color=WHITE), Dot(e,.04,color=WHITE))
        return g.set_opacity(opacity)

    def target(self, xy, name="TARGET"):
        pos = self.axes.c2p(*xy)
        marker = VGroup(Circle(radius=.15, color=ORANGE, stroke_width=3).move_to(pos),
                        Line(pos+LEFT*.21,pos+RIGHT*.21,color=ORANGE,stroke_width=2),
                        Line(pos+DOWN*.21,pos+UP*.21,color=ORANGE,stroke_width=2))
        if name:
            marker.add(label(name,17,ORANGE).next_to(marker,UR,buff=.09))
        return marker

    def item(self, text, y, math=False, size=28, color=INK):
        m = equation(text, size) if math else label(text, size, color)
        if m.width > 5.6:
            m.scale_to_fit_width(5.6)
        return m.move_to([3.2,y,0])

    def beat(self, li, reveal=None, motion=None):
        rec = next(r for r in self.records if r["chapter"] == self.ci and r["line"] == li)
        start = self.time
        with self.voiceover(text=rec["text"]):
            remaining = rec["duration"]
            if reveal is not None:
                self.play(FadeIn(reveal, shift=UP*.08), run_time=.6)
                remaining -= .6
            if motion:
                # Animated frames use ceil-like arange; frozen waits use floor.
                self.play(*motion, run_time=round(remaining, 9) - 1e-7)
            else:
                dynamic = self.ci == 8
                self.wait(round(remaining, 9) + (-1e-7 if dynamic else 1e-7), frozen_frame=not dynamic)
        self.actual_timeline.append({"chapter":self.ci,"line":li,"start":start,"end":self.time})

    def chapter_intro(self):
        self.rig(-20*DEGREES,100*DEGREES)
        target = self.target(fk(30*DEGREES,60*DEGREES))
        self.add(target)
        a = self.item("목표 위치 → 관절 각도",1.65,size=32)
        self.beat(0,reveal=a,motion=[self.q1.animate.set_value(30*DEGREES),self.q2.animate.set_value(60*DEGREES)])
        self.beat(1,reveal=self.item(r"\mathbf{p}=(x,y)\quad\longrightarrow\quad\mathbf{q}=(\theta_1,\theta_2)",.5,True,34))
        self.beat(2,reveal=self.item("2개의 회전 관절 · 2개의 링크",-.65,color=MUTED))
        self.beat(3,reveal=self.item("FK → IK → Trajectory",-1.75,size=31,color=GREEN))

    def chapter_setup(self):
        self.rig()
        self.beat(0,reveal=self.item("원점 = 로봇 베이스",1.8,size=30))
        self.beat(1,reveal=VGroup(self.item(r"L_1=1.0\,\mathrm{m}",.95,True,38),self.item(r"L_2=0.8\,\mathrm{m}",.25,True,38)))
        o=self.axes.c2p(0,0); e=self.axes.c2p(np.cos(PI/6),np.sin(PI/6))
        arcs=VGroup(Arc(radius=.5,start_angle=0,angle=PI/6,arc_center=o,color=BLUE),
            Arc(radius=.4,start_angle=PI/6,angle=PI/3,arc_center=e,color=PURPLE),
            DashedLine(e,e+np.array([.75*np.cos(PI/6),.75*np.sin(PI/6),0]),color=MUTED),
            equation(r"\theta_1",26).move_to(o+[.7,.17,0]), equation(r"\theta_2",26).move_to(e+[.48,.5,0]))
        self.beat(2,reveal=arcs)
        self.beat(3,reveal=VGroup(self.item(r"\phi_2=\theta_1+\theta_2",-.8,True,39),self.item("반시계 방향 + / θ₂는 상대 각도",-1.75,size=24,color=MUTED)))

    def chapter_fk(self):
        self.rig(25*DEGREES,40*DEGREES)
        self.beat(0,reveal=self.item("Forward Kinematics",1.85,size=30,color=BLUE))
        def projections():
            a,b=self.q1.get_value(),self.q2.get_value()
            e=self.axes.c2p(np.cos(a),np.sin(a)); p=self.axes.c2p(*fk(a,b)); o=self.axes.c2p(0,0)
            return VGroup(DashedLine(o,[e[0],o[1],0],color=BLUE),DashedLine([e[0],o[1],0],e,color=BLUE),
                          DashedLine(e,[p[0],e[1],0],color=PURPLE),DashedLine([p[0],e[1],0],p,color=PURPLE))
        proj=always_redraw(projections)
        self.add(proj)
        self.beat(1,reveal=self.item(r"x=L_1\cos\theta_1+L_2\cos(\theta_1+\theta_2)",.8,True,34))
        self.beat(2,reveal=self.item(r"y=L_1\sin\theta_1+L_2\sin(\theta_1+\theta_2)",-.2,True,34))
        self.beat(3,reveal=self.item("각도를 넣으면 좌표가 나온다",-1.55,color=GREEN),
            motion=[self.q1.animate.set_value(65*DEGREES),self.q2.animate.set_value(-50*DEGREES)])

    def chapter_numeric(self):
        self.rig(10*DEGREES,25*DEGREES)
        self.beat(0,reveal=self.item(r"\theta_1=30^\circ,\quad\theta_2=60^\circ",1.8,True,39),
            motion=[self.q1.animate.set_value(PI/6),self.q2.animate.set_value(PI/3)])
        self.beat(1,reveal=VGroup(self.item(r"x=1\cos30^\circ+0.8\cos90^\circ",.8,True,33),self.item(r"x\approx0.866\,\mathrm{m}",.1,True,37)))
        self.beat(2,reveal=self.item(r"y=1\sin30^\circ+0.8\sin90^\circ=1.3\,\mathrm{m}",-.75,True,32))
        self.beat(3,reveal=VGroup(self.target(fk(PI/6,PI/3),"(0.866, 1.300)"),self.item("각도 → 계산된 손끝 위치",-1.8,color=GREEN)))

    def chapter_ik(self):
        self.rig()
        p=fk(PI/6,PI/3)
        self.add(self.target(p))
        triangle=DashedLine(self.axes.c2p(0,0),self.axes.c2p(*p),color=GREEN,stroke_width=3)
        self.beat(0,reveal=VGroup(triangle,self.item("Inverse Kinematics",1.95,size=30,color=GREEN)))
        self.beat(1,reveal=self.item(r"D=\frac{x^2+y^2-L_1^2-L_2^2}{2L_1L_2}=\cos\theta_2",.9,True,37))
        self.beat(2,reveal=self.item(r"\theta_2=\operatorname{atan2}\!\left(\pm\sqrt{1-D^2},D\right)",-.25,True,35))
        self.beat(3,reveal=VGroup(self.item(r"\theta_1=\operatorname{atan2}(y,x)",-1.22,True,32),
            self.item(r"-\operatorname{atan2}(L_2\sin\theta_2,L_1+L_2\cos\theta_2)",-1.85,True,30)))

    def chapter_branches(self):
        self.rig()
        p=fk(PI/6,PI/3); other=ik(*p,branch=-1)
        self.add(self.target(p))
        self.beat(0,reveal=self.item(r"A:\ (30^\circ,\ 60^\circ)",1.7,True,40))
        ghost=self.robot(PI/6,PI/3,.23)
        self.add(ghost)
        self.beat(1,reveal=self.item(r"B:\ (82.66^\circ,\ {-60^\circ})",.7,True,40),
            motion=[self.q1.animate.set_value(other[0]),self.q2.animate.set_value(other[1])])
        self.beat(2,reveal=self.item("같은 위치, 서로 다른 팔꿈치",-.45,size=29,color=GREEN))
        self.beat(3,reveal=VGroup(self.item("관절 제한 / 충돌 여부",-1.4,size=26),self.item("현재 자세로부터의 이동량",-1.95,size=26,color=MUTED)))

    def chapter_workspace(self):
        self.rig(0,0)
        scale=self.axes.x_axis.unit_size
        outer=Circle(radius=(L1+L2)*scale,color=GREEN,stroke_width=3).move_to(self.axes.c2p(0,0))
        inner=Circle(radius=abs(L1-L2)*scale,color=RED,stroke_width=3).move_to(self.axes.c2p(0,0))
        self.beat(0,reveal=VGroup(outer,self.item(r"r_{\max}=L_1+L_2=1.8\,\mathrm{m}",1.65,True,36)))
        self.beat(1,reveal=VGroup(inner,self.item(r"r_{\min}=|L_1-L_2|=0.2\,\mathrm{m}",.75,True,36)),motion=[self.q2.animate.set_value(PI)])
        area=Annulus(inner_radius=.2*scale,outer_radius=1.8*scale,fill_color=GREEN,fill_opacity=.09,stroke_width=0).move_to(self.axes.c2p(0,0))
        self.add(area)
        self.bring_to_front(self.arm)
        self.beat(2,reveal=self.item(r"0.2\leq\sqrt{x^2+y^2}\leq1.8",-.35,True,37))
        self.beat(3,reveal=VGroup(self.target((1.7,1.1),"NO IK"),self.item(r"|D|>1\quad\Rightarrow\quad\text{no real solution}",-1.45,True,33),self.item("관절 제한과 충돌을 무시한 영역",-2.0,size=22,color=MUTED)))

    def chapter_trajectory(self):
        start=np.array([-25,100])*DEGREES; end=np.array([65,20])*DEGREES
        self.rig(*start)
        self.beat(0,reveal=self.item(r"\mathbf{q}(t)=\mathbf{q}_0+s(t)(\mathbf{q}_f-\mathbf{q}_0)",1.75,True,34))
        self.beat(1,reveal=VGroup(self.item(r"\tau=t/T,\quad s=3\tau^2-2\tau^3",.8,True,36),
            self.item(r"\dot{s}(0)=\dot{s}(T)=0",.05,True,35)))
        curve=ParametricFunction(lambda t:self.axes.c2p(*fk(*(start+t*(end-start)))),t_range=[0,1],color=GREEN,stroke_width=4)
        straight=DashedLine(self.axes.c2p(*fk(*start)),self.axes.c2p(*fk(*end)),color=MUTED,stroke_width=2)
        self.add(straight)
        self.beat(2,reveal=self.item("초록: 손끝 궤적 / 회색: 직선",-.9,size=24,color=GREEN),
            motion=[Create(curve,rate_func=lambda t:3*t*t-2*t*t*t),
                    self.q1.animate(rate_func=lambda t:3*t*t-2*t*t*t).set_value(end[0]),
                    self.q2.animate(rate_func=lambda t:3*t*t-2*t*t*t).set_value(end[1])])
        self.beat(3,reveal=self.item("기구학 예시 · 충돌 검사 미포함",-1.85,size=24,color=MUTED))

    def chapter_jacobian(self):
        self.rig(25*DEGREES,55*DEGREES)
        self.beat(0,reveal=VGroup(self.item(r"\dot{\mathbf{p}}=J(\mathbf{q})\dot{\mathbf{q}}",1.8,True,43),
            self.item(r"s_1=\sin\theta_1,\quad s_{12}=\sin(\theta_1+\theta_2)",1.08,True,25),
            self.item(r"c_1=\cos\theta_1,\quad c_{12}=\cos(\theta_1+\theta_2)",.65,True,25)))
        self.beat(1,reveal=self.item(r"J=\begin{bmatrix}-L_1s_1-L_2s_{12}&-L_2s_{12}\\L_1c_1+L_2c_{12}&L_2c_{12}\end{bmatrix}",-.18,True,32))
        self.beat(2,reveal=self.item(r"\dot{\mathbf{q}}=\begin{bmatrix}0.3\\0.2\end{bmatrix}\,\mathrm{rad/s}",-1.22,True,33))
        def velocity():
            a,b=self.q1.get_value(),self.q2.get_value(); p=fk(a,b)
            v=jacobian(a,b)@np.array([.3,.2])
            return Arrow(self.axes.c2p(*p),self.axes.c2p(*(p+v)),buff=0,color=GREEN,stroke_width=6,max_tip_length_to_length_ratio=.2)
        self.add(always_redraw(velocity))
        # Change configuration at exactly the displayed joint speeds.
        rec=next(r for r in self.records if r["chapter"]==self.ci and r["line"]==3)
        t=rec["duration"]-.6
        self.beat(3,reveal=self.item("화살표: v × 1 s (속도 표시)",-2.02,size=21,color=GREEN),
            motion=[self.q1.animate(rate_func=linear).increment_value(.3*t),self.q2.animate(rate_func=linear).increment_value(.2*t)])

    def chapter_singular(self):
        self.rig(0,35*DEGREES)
        self.beat(0,reveal=self.item("Singularity",1.8,size=32,color=RED),motion=[self.q2.animate.set_value(0)])
        self.beat(1,reveal=VGroup(self.item(r"\det J=L_1L_2\sin\theta_2",.85,True,39),self.item(r"\theta_2=0,\pi\quad\Rightarrow\quad\det J=0",.0,True,35)))
        p=self.axes.c2p(1.8,0)
        arrows=VGroup(DoubleArrow(p+DOWN*.72,p+UP*.72,color=GREEN,buff=0,stroke_width=5),
            DashedLine(p+LEFT*.6,p+RIGHT*.25,color=RED,stroke_width=4))
        self.beat(2,reveal=VGroup(arrows,self.item("초록: 가능한 순간 속도 방향",-.95,size=24,color=GREEN),self.item("빨강: 순간적으로 만들 수 없는 방향",-1.5,size=23,color=RED)))
        self.beat(3,reveal=self.item("특이점 근처의 속도 요구에 주의",-2.05,size=23,color=MUTED))

    def pipeline_box(self, title, subtitle, x, y, color):
        box=RoundedRectangle(width=3.6,height=1.15,corner_radius=.14,fill_color=WHITE,fill_opacity=1,stroke_color=color,stroke_width=2).move_to([x,y,0])
        return VGroup(box,label(title,27,color).move_to([x,y+.19,0]),label(subtitle,19,MUTED).move_to([x,y-.26,0]))

    def chapter_pipeline(self):
        a=self.pipeline_box("인식 + 깊이","Camera → 3D point",-4.4,1.3,BLUE)
        b=self.pipeline_box("좌표 변환","Camera frame → Base frame",0,1.3,BLUE)
        c=self.pipeline_box("집기 목표","Position + Orientation",4.4,1.3,PURPLE)
        d=self.pipeline_box("IK","목표 자세 → 관절 각도",-4.4,-.65,GREEN)
        e=self.pipeline_box("Motion Planning","충돌 회피 + 시간 궤적",0,-.65,GREEN)
        f=self.pipeline_box("Control → Robot","관절 상태 피드백",4.4,-.65,ORANGE)
        def arrow(x,y):return Arrow(x.get_right(),y.get_left(),buff=.12,color=MUTED,stroke_width=3)
        self.beat(0,reveal=VGroup(a,b,arrow(a,b)))
        self.beat(1,reveal=VGroup(c,arrow(b,c)))
        flow=VGroup(Line([4.4,.65,0],[4.4,.22,0],color=MUTED),Line([4.4,.22,0],[-4.4,.22,0],color=MUTED),Arrow([-4.4,.22,0],[-4.4,-.06,0],buff=0,color=MUTED,max_tip_length_to_length_ratio=.5))
        self.beat(2,reveal=VGroup(d,e,arrow(d,e),flow))
        self.beat(3,reveal=VGroup(f,arrow(e,f),label("이번 영상: 평면 2관절의 위치 기구학",24,MUTED).move_to([0,-2.03,0])))

    def chapter_recap(self):
        self.rig(PI/6,PI/3)
        self.beat(0,reveal=VGroup(self.item("FK   각도 → 위치",1.7,size=31,color=BLUE),self.item("IK   위치 → 각도",.85,size=31,color=GREEN)))
        self.beat(1,reveal=self.item("해의 개수 / 작업 공간 / 자세 선택",-.1,size=25))
        self.beat(2,reveal=self.item("각도 → 시간 궤적 → 제어",-1.0,size=28,color=GREEN))
        self.beat(3,reveal=VGroup(self.item(r"(0^\circ,90^\circ)\Rightarrow(1.0,0.8)\,\mathrm{m}",-1.9,True,33),self.target((1,.8),"(1.0, 0.8)")),
            motion=[self.q1.animate.set_value(0),self.q2.animate.set_value(PI/2)])
