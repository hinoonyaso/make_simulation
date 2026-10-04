"""Portrait Manim edit of eight narrated QLoRA highlights, pitch-preserving 1.3x."""
import json
from pathlib import Path
import numpy as np
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.base import SpeechService

config.frame_width=9
config.frame_height=16
ROOT=Path(__file__).resolve().parent
BG,INK,MUTED,BLUE,PURPLE,GREEN,ORANGE='#F7F9FC','#202D43','#65738A','#2676D5','#8255C7','#198F70','#ED941D'


def txt(s,size=38,color=INK,width=6.6):
    m=Text(s,font='NanumGothic',font_size=size,color=color,line_spacing=.9)
    if m.width>width:m.scale_to_fit_width(width)
    return m


def eq(s,size=49):
    m=MathTex(s,font_size=size,color=INK)
    if m.width>6.6:m.scale_to_fit_width(6.6)
    return m


def card(title,sub='',color=BLUE,w=6.4):
    return VGroup(RoundedRectangle(width=w,height=1.15,corner_radius=.15,color=color,fill_color=WHITE,fill_opacity=1),
        txt(title,38,color,w-.3).move_to([0,.18 if sub else 0,0]),
        txt(sub,25,MUTED,w-.3).move_to([0,-.31,0]) if sub else VGroup())


def tiles(rows,cols,color=PURPLE,cell=.24,seed=1):
    rng=np.random.default_rng(seed)
    return VGroup(*[Square(side_length=cell,stroke_color=WHITE,stroke_width=1,
        fill_color=color,fill_opacity=float(rng.uniform(.15,1))) for _ in range(rows*cols)]).arrange_in_grid(rows=rows,cols=cols,buff=.025)


class Speech(SpeechService):
    def __init__(self,recs):
        super().__init__(cache_dir=str(ROOT/'assets/audio'));self.recs={r['text']:r for r in recs}
    def generate_from_text(self,text,cache_dir=None,path=None,**kwargs):
        return {'input_text':text,'input_data':{'input_text':text,'service':'qlora-short-1.3'},'original_audio':Path(self.recs[text]['audio']).name}


class QLoRAShort(VoiceoverScene):
    def construct(self):
        self.camera.background_color=BG
        recs=json.loads((ROOT/'assets/audio/manifest.json').read_text());self.set_speech_service(Speech(recs),create_subcaption=False)
        titles=['모두 다시 학습해야 할까?','기본 지식 + 작은 수정','변화량을 작은 두 행렬로','저장 정밀도 ≠ 계산 정밀도','같은 입력, 두 개의 경로','무엇이 업데이트될까?','가중치 용량 ≠ 전체 VRAM','세 가지로 기억하자']
        timeline=[]
        for i,r in enumerate(recs):
            self.clear()
            self.add(txt('QLoRA',96,PURPLE).move_to([-.3,5.9,0]),txt('핵심 1분  /  FAST EXPLAINER',24,MUTED).move_to([-.3,4.65,0]),
                txt(titles[i],36,INK).move_to([-.3,3.6,0]),txt(f'{i+1:02} / 08',20,MUTED).move_to([-.3,-6.1,0]))
            for j in range(8):self.add(Line([-3.6+j*.85,-6.5,0],[-2.88+j*.85,-6.5,0],color=PURPLE if j<=i else '#DDE5EF',stroke_width=5))
            body,motion=getattr(self,f'scene_{i}')()
            start=self.time
            with self.voiceover(text=r['text']):
                self.play(FadeIn(body,shift=UP*.08),run_time=.5)
                self.play(*motion,run_time=1.2-1e-7)
                self.wait(round(r['duration']-1.7,9)+1e-7,frozen_frame=True)
            timeline.append(dict(start=start,end=self.time))
        (ROOT/'output/timeline.json').write_text(json.dumps(timeline,indent=2))

    def scene_0(self):
        matrix=tiles(8,8,BLUE,.37).move_to([-.3,.65,0])
        body=VGroup(matrix,txt('거대한 언어 모델',38,BLUE).move_to([-.3,-1.55,0]))
        return body,[Indicate(matrix,color=PURPLE)]

    def scene_1(self):
        a=card('FROZEN BASE','4-bit NF4',BLUE).move_to([-.3,1.8,0]);b=card('TRAINABLE LoRA','새로운 변화만 학습',PURPLE).move_to([-.3,-1.1,0])
        return VGroup(a,b,txt('+',65).move_to([-.3,.3,0])),[Indicate(b,color=PURPLE)]

    def scene_2(self):
        b=tiles(8,2,PURPLE,.3).move_to([-2,.7,0]);a=tiles(2,8,GREEN,.3).move_to([.95,.7,0])
        body=VGroup(b,a,txt('B',35,PURPLE).next_to(b,UP),txt('A',35,GREEN).next_to(a,UP),eq(r'\Delta W=\frac{\alpha}{r}BA').move_to([-.3,-1.45,0]))
        return body,[Indicate(a,color=GREEN),Indicate(b,color=PURPLE)]

    def scene_3(self):
        a=card('4-bit NF4','기본 가중치를 작게 저장',BLUE).move_to([-.3,1.75,0]);b=card('BF16 / FP16','필요한 가중치를 역양자화해 계산',ORANGE).move_to([-.3,-1.2,0])
        return VGroup(a,b,Arrow([-.3,.95,0],[-.3,-.4,0],color=ORANGE,buff=.03)),[Indicate(b,color=ORANGE)]

    def scene_4(self):
        x=txt('x',45,ORANGE).move_to([-.3,2.5,0]);a=card('BASE','dequant(W₄)x',BLUE,2.85).move_to([-2,.85,0]);b=card('LoRA','(α/r) B(Ax)',PURPLE,2.85).move_to([1.4,.85,0])
        plus=VGroup(Circle(radius=.29,color=INK),txt('+',38)).move_to([-.3,-.8,0])
        links=VGroup(Arrow(x.get_bottom(),a.get_top(),buff=.13,color=BLUE),Arrow(x.get_bottom(),b.get_top(),buff=.13,color=PURPLE),
            Arrow(a.get_bottom(),plus.get_left(),buff=.12,color=BLUE),Arrow(b.get_bottom(),plus.get_right(),buff=.12,color=PURPLE))
        return VGroup(x,a,b,plus,links,eq(r'y=\operatorname{dequant}(W_4)x+\frac{\alpha}{r}B(Ax)',36).move_to([-.3,-2.1,0])),[Indicate(plus,color=GREEN)]

    def scene_5(self):
        base=tiles(8,8,BLUE,.25).move_to([-1.95,.65,0]);adapter=tiles(4,3,PURPLE,.34).move_to([1.35,.65,0])
        body=VGroup(base,adapter,txt('고정',32,BLUE).move_to([-1.95,2.1,0]),txt('A, B',32,PURPLE).move_to([1.35,2.1,0]),
            card('UPDATE','교육용 색상 변화',PURPLE).move_to([-.3,-1.6,0]))
        return body,[Transform(adapter,tiles(4,3,PURPLE,.34,seed=9).move_to(adapter))]

    def scene_6(self):
        a=Rectangle(width=5.6,height=.65,stroke_width=0,fill_color=BLUE,fill_opacity=1).move_to([-3.15,1.2,0],aligned_edge=LEFT)
        b=Rectangle(width=1.4,height=.65,stroke_width=0,fill_color=PURPLE,fill_opacity=1).move_to([-3.15,-.3,0],aligned_edge=LEFT)
        body=VGroup(a,b,txt('7B · 가중치 표현만 비교',27,MUTED).move_to([-.3,2.25,0]),txt('16-bit  /  14 GB',30,WHITE).move_to(a),
            txt('4-bit  /  3.5 GB',30,PURPLE).next_to(b,RIGHT,buff=.15),card('+ 추가 메모리','스케일 · LoRA · 기울기 · 활성값 등',ORANGE).move_to([-.3,-1.9,0]))
        return body,[Indicate(b,color=PURPLE)]

    def scene_7(self):
        cards=VGroup(card('STORE','4-bit NF4',BLUE),card('COMPUTE','BF16 / FP16',ORANGE),card('UPDATE','LoRA A, B',PURPLE)).arrange(DOWN,buff=.55).move_to([-.3,.1,0])
        return cards,[Indicate(cards[0],color=BLUE),Indicate(cards[2],color=PURPLE)]
