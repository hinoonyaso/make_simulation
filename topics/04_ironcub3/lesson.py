"""Manim presentation; Blender images are composited into reserved spatial panels."""
import json, os
from pathlib import Path
import numpy as np
from manim import *

ROOT=Path(__file__).resolve().parent
BG,INK,MUTED='#F7F9FC','#202D43','#65738A'
BLUE,GREEN,ORANGE,RED,PURPLE='#2676D5','#198F70','#ED941D','#D34F55','#8255C7'
FONT='NanumGothic'
def txt(s,size=30,color=INK,width=12):
    t=Text(s,font=FONT,font_size=size,color=color)
    if t.width>width:t.scale_to_fit_width(width)
    return t
def eq(s,size=42,color=INK):return MathTex(s,font_size=size,color=color)
def box(title,sub='',color=BLUE,w=3.5,h=1.2):
    b=RoundedRectangle(width=w,height=h,corner_radius=.15,stroke_color=color,fill_color=WHITE,fill_opacity=1)
    t=txt(title,29,color,w-.3).move_to([0,.19 if sub else 0,0])
    return VGroup(b,t,*([txt(sub,19,MUTED,w-.3).move_to([0,-.28,0])] if sub else []))
def xy(x,y):return np.array([(x-960)/135,(540-y)/135,0])

class FlyingHumanoid(Scene):
    def construct(self):
        self.camera.background_color=BG
        self.doc=json.loads((ROOT/'storyboard.json').read_text())
        self.records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
        self.sim=json.loads((ROOT/'output/simulation.json').read_text())
        only=os.getenv('LESSON_CHAPTER')
        if not only:self.add_sound(str(ROOT/'output/narration.wav'))
        timeline=[]
        for ci,ch in enumerate(self.doc['chapters']):
            if only and ch['id']!=only:continue
            self.clear()
            self.add(txt('PAPER → ALGORITHM → ROBOT',19,PURPLE).to_corner(UL,buff=.36),
                txt(f'{ci+1:02d} / 09',20,MUTED).to_corner(UR,buff=.36),
                txt(ch['title'],36,width=13).move_to([0,2.95,0]),
                Line([-6.75,2.53,0],[6.75,2.53,0],color='#DDE5EF'),
                txt('iRonCub 3 · Gorbani et al., 2025 · arXiv:2506.01125v1',16,MUTED).move_to([0,-3.02,0]))
            self.rs=[r for r in self.records if r['chapter']==ci]
            timeline.append(dict(chapter=ci,id=ch['id'],start=self.time,duration=sum(r['duration'] for r in self.rs)))
            getattr(self,'scene_'+ch['id'])()
        if not only:(ROOT/'output/render_timeline.json').write_text(json.dumps(timeline,indent=2))

    def beat(self,i,*animations):
        d=self.rs[i]['duration']
        if animations:
            t=min(1.2,d);self.play(*animations,run_time=t);self.wait(max(.001,d-t))
        else:self.wait(d)

    def hero_slot(self):
        # Exact FFmpeg overlay: x=60,y=255,w=1000,h=622.
        self.add(RoundedRectangle(width=1000/135,height=622/135,corner_radius=.1,
            stroke_color='#DDE5EF',fill_color=BG,fill_opacity=1).move_to(xy(560,566)))

    def scene_hook(self):
        self.hero_slot()
        title=txt('iRonCub 3',54,PURPLE,width=5.4).move_to([3.85,1.45,0])
        q=txt('뜨는 힘\n균형을 잡는 계산',35,width=5.4).move_to([3.8,.25,0])
        self.beat(0,FadeIn(title),FadeIn(q))
        paper=box('2025 · 첫 이륙 연구','구조 + 추정 + 모델 예측 제어',BLUE,w=5.4).move_to([3.75,-1.15,0])
        self.beat(1,FadeIn(paper))
        note=txt('직접 제작한 구조 모형\n실제 시험 영상이 아닙니다',22,MUTED,width=5.4).move_to([3.75,-2.25,0])
        self.beat(2,FadeIn(note))

    def scene_platform(self):
        self.hero_slot()
        cards=VGroup(box('4 JETS','팔 2개 + 등 2개',BLUE,w=5.3),
            box('POSITION × FORCE','어디에서, 어느 방향으로 미는가?',ORANGE,w=5.3),
            box('TOY MODEL · 50 kg','질량·관성·배치는 설명용 가정',PURPLE,w=5.3)).arrange(DOWN,buff=.3).move_to([3.85,.15,0])
        for i in range(3):self.beat(i,FadeIn(cards[i],shift=UP*.1))

    def scene_force(self):
        formula=eq(r'm\ddot z=\sum_i F_{z,i}-mg',54).move_to([0,1.8,0])
        body=RoundedRectangle(width=1.5,height=1.8,fill_color='#DBE8F7',fill_opacity=1,stroke_color=BLUE).move_to([-3,-.3,0])
        up=Arrow([-3,.6,0],[-3,1.5,0],color=GREEN,buff=0)
        down=Arrow([-3,-1.2,0],[-3,-2.1,0],color=RED,buff=0)
        self.beat(0,Write(formula),FadeIn(VGroup(body,up,down)))
        numbers=VGroup(eq(r'mg=50\times9.81=490.5\;\mathrm{N}',35),
            eq(r'T_i=\frac{mg}{4}=122.6\;\mathrm{N}',35,color=BLUE)).arrange(DOWN,buff=.5).move_to([2,.05,0])
        self.beat(1,FadeIn(numbers))
        tilted=eq(r'F_z=T\cos\theta,\qquad F_x=T\sin\theta',35,color=ORANGE).move_to([1.65,-1.9,0])
        self.beat(2,Rotate(VGroup(body,up),-.3,about_point=np.array([-3,-.3,0])),FadeIn(tilted))

    def scene_torque(self):
        formula=eq(r'\tau=\sum_i(r_i-r_{\mathrm{CoM}})\times F_i',49).move_to([0,1.8,0])
        bar=Line([-3,-.5,0],[3,-.5,0],stroke_width=12,color=MUTED)
        center=Dot([0,-.5,0],color=PURPLE,radius=.12)
        left=Arrow([-3,-.5,0],[-3,.8,0],buff=0,color=BLUE)
        right=Arrow([3,-.5,0],[3,.8,0],buff=0,color=BLUE)
        labels=VGroup(txt('LEFT PAIR',22,BLUE).move_to([-3,-1.1,0]),txt('RIGHT PAIR',22,BLUE).move_to([3,-1.1,0]),txt('CoM',22,PURPLE).move_to([0,-1,0]))
        self.beat(0,Write(formula),FadeIn(VGroup(bar,center,left,right,labels)))
        alt=eq(r'I\ddot\theta=\ell(T_L-T_R)',43,color=ORANGE).move_to([0,-2,0])
        self.beat(1,Transform(left,Arrow([-3,-.5,0],[-3,1.15,0],buff=0,color=ORANGE)),
            Transform(right,Arrow([3,-.5,0],[3,.45,0],buff=0,color=BLUE)),Write(alt))
        self.beat(2,Indicate(alt,color=ORANGE))

    def scene_delay(self):
        axes=Axes(x_range=[0,3.1,1],y_range=[0,1.1,.5],x_length=8,y_length=2.8,
            axis_config={'color':MUTED,'include_tip':False,'include_numbers':True,'font_size':20}).move_to([-1.9,-.25,0])
        axes.x_axis.numbers.set_color(MUTED)
        axes.y_axis.numbers.set_color(MUTED)
        labels=VGroup(txt('시간 [s]',20,MUTED).move_to([-1.9,-2.12,0]),txt('정규화 추력',20,MUTED).move_to([-5,1.43,0]))
        command=DashedLine(axes.c2p(0,1),axes.c2p(3,1),color=MUTED)
        self.beat(0,Create(axes),FadeIn(labels),Create(command))
        a=axes.plot(lambda t:1-np.exp(-t/.35),x_range=[0,3],color=BLUE)
        b=axes.plot(lambda t:1-np.exp(-t/.77),x_range=[0,3],color=ORANGE)
        legends=VGroup(txt('τ = 0.35 s',25,BLUE),txt('τ = 0.77 s',25,ORANGE),txt('교육용 1차 지연',21,MUTED)).arrange(DOWN,buff=.35).move_to([4.55,.3,0])
        f=eq(r'\tau\dot T+T=T_{\mathrm{cmd}}',43).move_to([0,1.9,0])
        self.beat(1,Create(a),Create(b),FadeIn(legends),Write(f))
        note=txt('실제 논문의 제트 모델은 비선형 2차 모델',25,PURPLE).move_to([0,-2.6,0])
        self.beat(2,FadeIn(note))

    def scene_mpc(self):
        formula=eq(r'\min_{u_{0:N-1}}\sum_{k=1}^{N}\|s_k-s_k^*\|_Q^2+\sum_{k=0}^{N-1}\|u_k\|_R^2',36).move_to([0,1.9,0])
        blocks=VGroup(*[box(t,s,c,w=2.8) for t,s,c in [('STATE','지금의 상태',BLUE),('PREDICT','미래 반응',PURPLE),('OPTIMIZE','오차 + 제약',ORANGE),('EXECUTE','첫 명령만',GREEN)]]).arrange(RIGHT,buff=.5).move_to([0,.15,0])
        arrows=VGroup(*[Arrow(blocks[i].get_right(),blocks[i+1].get_left(),buff=.05,color=MUTED) for i in range(3)])
        notation=txt('s: 상태  ·  s*: 목표  ·  u: 명령  ·  Q/R: 비용 가중치',20,MUTED).move_to([0,1.05,0])
        self.beat(0,Write(formula),FadeIn(notation),FadeIn(blocks),Create(arrows))
        feedback=CurvedArrow(blocks[3].get_bottom()+DOWN*.15,blocks[0].get_bottom()+DOWN*.15,angle=-.55,color=BLUE)
        self.beat(1,Create(feedback))
        rates=txt('논문: 제트 명령 10 Hz  /  관절 저수준 제어 1000 Hz',27,PURPLE).move_to([0,-2.15,0])
        self.beat(2,FadeIn(rates))
        toy=txt('자체 실험: 평면 MPC · 관절/UKF 생략 · 이상적 상태 피드백',24,MUTED).move_to([0,-2.6,0])
        self.beat(3,FadeIn(toy))

    def scene_experiment(self):
        self.add(txt('모델 일치 · τ = 0.35 s',28,BLUE).move_to(xy(490,225)),
            txt('모델 불일치 · τ = 0.77 s',28,ORANGE).move_to(xy(1430,225)))
        for x in [490,1430]:self.add(Rectangle(width=900/135,height=560/135,stroke_color='#DDE5EF').move_to(xy(x,540)))
        self.add(txt('두 제어기의 예측 τ = 0.35 s · 3초 예측 · 10 Hz 갱신 · 동일한 목표',22,MUTED).move_to(xy(960,866)))
        self.beat(0)
        # Composite plays each 12-second trace beginning with utterance 1.
        self.beat(1)
        self.beat(2)
        values=[]
        for x,mode,color in [(490,'nominal',BLUE),(1430,'mismatch',ORANGE)]:
            m=self.sim[mode]['metrics']
            values.append(txt(f"위치 RMSE {m['position_rmse_m']*100:.2f} cm  |  최대 기울기 {m['max_pitch_deg']:.2f}°",25,color,width=6.5).move_to(xy(x,910)))
        self.beat(3,*[FadeIn(v) for v in values])

    def scene_evidence(self):
        a=box('PAPER · SIMULATION','완만한 경로 추종',BLUE,w=5.7,h=1.5).move_to([-3.25,1,0])
        b=box('PAPER · HARDWARE','짧은 이륙 · 접지 · 재이륙 · 정지',ORANGE,w=5.7,h=1.5).move_to([3.25,1,0])
        self.beat(0,FadeIn(a),FadeIn(b))
        causes=VGroup(*[box(t,'',c,w=3.6) for t,c in [('모델 오차',PURPLE),('센서 진동',BLUE),('추력 추정',ORANGE)]]).arrange(RIGHT,buff=.45).move_to([0,-.85,0])
        self.beat(1,FadeIn(causes))
        takeaway=txt('첫 이륙의 성과 + 실제 시스템에서 드러난 한계',33,width=12).move_to([0,-2.3,0])
        self.beat(2,FadeIn(takeaway))

    def scene_system(self):
        chain=VGroup(*[box(t,s,c,w=2.8) for t,s,c in [('SENSE','상태를 측정',BLUE),('ESTIMATE','상태·추력 추정',PURPLE),('CONTROL','미래를 예측',ORANGE),('ACTUATE','실제 힘 발생',GREEN)]]).arrange(RIGHT,buff=.5).move_to([0,.7,0])
        self.beat(0,FadeIn(chain))
        constraint=txt('주기 · 지연 · 단위 · 좌표계 · 피드백',37,PURPLE).move_to([0,-.6,0])
        self.beat(1,FadeIn(constraint))
        recap=VGroup(txt('힘의 합',32,BLUE),txt('회전 모멘트',32,ORANGE),txt('지연을 고려한 예측',32,GREEN)).arrange(RIGHT,buff=.75).move_to([0,-1.95,0])
        self.beat(2,FadeIn(recap))

class Thumbnail(Scene):
    def construct(self):
        self.camera.background_color=BG
        self.add(txt('PAPER × MATH × ROBOT SIMULATION',23,PURPLE).to_edge(UP,buff=.55))
        self.add(txt('iRonCub 3',76,PURPLE).move_to([-3,1.25,0]),
            txt('로봇은 어떻게\n균형을 잡고 날까?',45,width=7).move_to([-2.8,-.55,0]),
            txt('추력 · 회전 · MPC',29,BLUE).move_to([-3,-2.45,0]))
        self.add(Rectangle(width=5.6,height=5.0,stroke_width=0,fill_color=BG,fill_opacity=1).move_to([4,0,0]))
