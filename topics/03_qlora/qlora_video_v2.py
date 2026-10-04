"""Narration-led QLoRA lesson. See README.md for uv render commands."""
import json
import os
from pathlib import Path
import numpy as np
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.base import SpeechService

ROOT = Path(__file__).resolve().parent
BG, INK, MUTED = "#F7F9FC", "#202D43", "#65738A"
BLUE, PURPLE, GREEN, ORANGE, RED = "#2676D5", "#8255C7", "#198F70", "#ED941D", "#D34F55"
GRID, FONT = "#DDE5EF", "NanumGothic"
# NF4 codebook, normalized to [-1, 1], from bitsandbytes / QLoRA.
NF4 = np.array([-1., -.6961928, -.52507305, -.39491749, -.28444138,
    -.18477343, -.09105004, 0., .07958030, .16093020, .24611230,
    .33791524, .44070983, .56261700, .72295684, 1.])


def text(s, size=28, color=INK, width=None):
    m = Text(s, font=FONT, font_size=size, color=color, line_spacing=.8)
    if width and m.width > width:
        m.scale_to_fit_width(width)
    return m


def math(s, size=36, width=12, color=INK):
    m = MathTex(s, font_size=size, color=color)
    if m.width > width:
        m.scale_to_fit_width(width)
    return m


def card(title, sub="", color=BLUE, w=3.6, h=1.3):
    bg = RoundedRectangle(width=w, height=h, corner_radius=.16,
        fill_color=WHITE, fill_opacity=1, stroke_color=color, stroke_width=2)
    title_m = text(title, 29, color, w-.35).move_to([0, .2 if sub else 0, 0])
    items = [bg, title_m]
    if sub:
        items.append(text(sub, 20, MUTED, w-.35).move_to([0, -.29, 0]))
    return VGroup(*items)


def tag(s, color=BLUE, size=21):
    t = text(s, size, color)
    return VGroup(RoundedRectangle(width=t.width+.4, height=t.height+.24,
        corner_radius=.1, stroke_width=0, fill_color=color, fill_opacity=.09), t)


def heatmap(values, color=PURPLE, cell=.23, normalize=1):
    a = np.array(values)
    tiles = VGroup(*[Square(side_length=cell, stroke_color=WHITE, stroke_width=1.2,
        fill_color=interpolate_color(ManimColor("#EBEDF5"), ManimColor(color),
        float(np.clip(abs(v)/normalize, .08, 1))), fill_opacity=1)
        for v in a.flat]).arrange_in_grid(rows=a.shape[0], cols=a.shape[1], buff=.025)
    return tiles


def path(points, color=GRID, stroke=3):
    return VMobject(color=color, stroke_width=stroke).set_points_as_corners(
        [np.array([*p, 0.]) for p in points])


def toy_training():
    """Actual rank-2 least squares adapter training, frozen NF4 base, deterministic."""
    rng = np.random.default_rng(17)
    w = rng.normal(0, .3, (4, 4))
    scale = np.max(np.abs(w))
    codes = np.abs(w[..., None]/scale - NF4).argmin(axis=-1)
    base = NF4[codes]*scale
    x = rng.normal(size=(4, 32))
    target_update = rng.normal(0, .35, (4, 2)) @ rng.normal(0, .35, (2, 4))
    target = (base + target_update) @ x
    a, b = rng.normal(0, .25, (2, 4)), np.zeros((4, 2))
    frames = []
    for step in range(61):
        error = (base + b @ a) @ x - target
        loss = float(np.mean(error**2))
        frames.append(dict(step=step, loss=loss, A=a.tolist(), B=b.tolist()))
        g = 2 * error @ x.T / error.size
        da, db = b.T @ g, g @ a.T
        a, b = a-.6*da, b-.6*db
    return dict(base=base.tolist(), codes=codes.tolist(), scale=float(scale),
                rank=2, seed=17, lr=.6, frames=frames)


class PreparedSpeech(SpeechService):
    def __init__(self, records):
        super().__init__(cache_dir=str(ROOT / "assets/audio"))
        self.lookup = {r["text"]: r for r in records}

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        return {"input_text": text, "input_data": {"input_text": text, "service": "prepared-edge-tts"},
                "original_audio": Path(self.lookup[text]["audio"]).name}


class QLoRAEnhanced(VoiceoverScene):
    def construct(self):
        self.camera.background_color = BG
        self.doc = json.loads((ROOT / "storyboard.json").read_text())
        self.records = json.loads((ROOT / "assets/audio/manifest.json").read_text())
        self.set_speech_service(PreparedSpeech(self.records), create_subcaption=False)
        self.timeline = []
        self.sim = toy_training()
        (ROOT / "output/toy_training.json").write_text(json.dumps(self.sim, indent=2))
        selected = os.environ.get("LESSON_CHAPTER")
        for ci, ch in enumerate(self.doc["chapters"]):
            if selected and selected != ch["id"]:
                continue
            self.ci = ci
            self.clear()
            self.header(ch["title"])
            getattr(self, "chapter_" + ch["id"])()
        name = "preview_timeline" if selected else "render_timeline_v2"
        (ROOT / f"output/{name}.json").write_text(json.dumps(self.timeline, indent=2))

    def header(self, title):
        self.add(text("MACHINE LEARNING  /  QLoRA", 16, PURPLE).to_corner(UL, buff=.42))
        self.add(text(title, 35, width=12.7).move_to([-6.55, 3.02, 0], aligned_edge=LEFT))
        self.add(text(f"{self.ci+1:02d} / 09", 18, MUTED).to_corner(UR, buff=.42))
        self.add(Line([-6.55, 2.5, 0], [6.55, 2.5, 0], color=GRID, stroke_width=2))
        for i in range(9):
            self.add(Line([-6.55+i*1.46, -3.85, 0], [-5.24+i*1.46, -3.85, 0],
                          color=PURPLE if i <= self.ci else GRID, stroke_width=5))

    def beat(self, li, reveal=None, animations=None, seconds=2.4):
        rec = next(r for r in self.records if r["chapter"] == self.ci and r["line"] == li)
        start = self.time
        with self.voiceover(text=rec["text"]):
            remaining = rec["duration"]
            if reveal is not None:
                self.play(FadeIn(reveal, shift=UP*.08), run_time=.6)
                remaining -= .6
            if animations:
                nframes = min(round(seconds*config.frame_rate), int(remaining*config.frame_rate))
                span = nframes/config.frame_rate
                self.play(*animations, run_time=round(span, 9)-1e-7)
                remaining -= span
            if remaining > 1/config.frame_rate:
                self.wait(round(remaining, 9)+1e-7, frozen_frame=True)
        self.timeline.append(dict(chapter=self.ci, line=li, start=start, end=self.time,
                                  intended_duration=rec["duration"]))

    def foot(self, s, color=MUTED):
        return text(s, 20, color, width=12.4).move_to([0, -2.66, 0])

    def chapter_hook(self):
        self.add(text("QLoRA", 78, PURPLE).move_to([-3.55, 1.05, 0]))
        self.add(text("Quantized Low-Rank Adaptation", 23, MUTED).move_to([-3.55, .18, 0]))
        tiles = heatmap(np.random.default_rng(3).uniform(.1, 1, (8, 8)), BLUE, .25).move_to([3.5, .9, 0])
        bits = tag("16-bit", BLUE, 30).move_to([3.5, -.6, 0])
        self.beat(0, reveal=VGroup(tiles, bits, self.foot("사전 학습 모델을 내 작업에 맞게 바꾸는 방법")))
        adapter = tag("+ trainable LoRA", PURPLE, 22).next_to(tiles, RIGHT, buff=.2)
        if adapter.get_right()[0] > 6.45:
            adapter.next_to(tiles, DOWN, buff=1.0)
        self.beat(1, reveal=adapter, animations=[Transform(bits, tag("4-bit NF4", BLUE, 30).move_to(bits))])
        row = VGroup(card("저장", "4-bit 기본 가중치", BLUE, 3.7, 1.1),
                     card("계산", "BF16 / FP16", ORANGE, 3.7, 1.1),
                     card("학습", "작은 A, B 행렬", PURPLE, 3.7, 1.1)).arrange(RIGHT, buff=.45).move_to([0,-1.76,0])
        self.remove(adapter)
        self.beat(2, reveal=row)

    def chapter_rank(self):
        equation = math(r"\Delta W = \frac{\alpha}{r}\,B A", 45).move_to([0, 1.78, 0])
        self.add(equation)
        dense = heatmap(np.random.default_rng(1).uniform(.1,1,(8,8)), PURPLE, .245).move_to([-4.5,-.02,0])
        self.add(text("ΔW", 30, PURPLE).next_to(dense, UP, buff=.13))
        self.add(math(r"d_{out}\times d_{in}", 27).next_to(dense, DOWN, buff=.22))
        b = heatmap(np.ones((8,2))*.6,PURPLE,.245).move_to([-.5,-.02,0])
        a = heatmap(np.ones((2,8))*.6,GREEN,.245).move_to([2.25,-.02,0])
        group = VGroup(b,a,text("×",35,MUTED).move_to([.52,-.02,0]),
            math(r"B\;:\;d_{out}\times r",27,color=PURPLE).move_to([-.5,-1.46,0]),
            math(r"A\;:\;r\times d_{in}",27,color=GREEN).move_to([2.6,-1.46,0]),
            Arrow([-3.1,0,0],[-1.25,0,0],color=MUTED,buff=.1))
        self.beat(0,reveal=dense)
        self.beat(1,reveal=group,animations=[Indicate(a,color=GREEN),Indicate(b,color=PURPLE)])
        stat = card("16,777,216  →  131,072", "4096 × 4096, r = 16 · 이 층의 파라미터 수", PURPLE, 8.8, 1.05).move_to([0,-2.23,0])
        self.beat(2,reveal=stat)
        self.beat(3,reveal=tag("0.78125%",GREEN,30).move_to([5.1,.2,0]))

    def parallel_diagram(self):
        inp = tag("x", ORANGE, 35).move_to([-5.8,.35,0])
        base = card("dequant(W₄) · x", "동결된 기본 경로 · BF16 / FP16 계산", BLUE, 5.2, 1.2).move_to([-.75,1.18,0])
        a = card("A", "dᵢₙ → r", PURPLE, 1.6, 1.05).move_to([-2.45,-.7,0])
        b = card("B", "r → dₒᵤₜ", PURPLE, 1.6, 1.05).move_to([-.35,-.7,0])
        scale = tag("α/r",PURPLE,27).move_to([1.57,-.7,0])
        plus = VGroup(Circle(radius=.29,color=INK,fill_color=WHITE,fill_opacity=1),text("+",32)).move_to([3.8,.35,0])
        output = tag("y",GREEN,35).move_to([5.6,.35,0])
        upper = path([(-5.32,.35),(-4.2,.35),(-4.2,1.18),(-3.35,1.18)],BLUE)
        upper2 = path([(1.85,1.18),(3.25,1.18),(3.25,.35),(3.51,.35)],BLUE)
        lower = path([(-4.2,.35),(-4.2,-.7),(-3.25,-.7)],PURPLE)
        lower2 = path([(2.08,-.7),(3.25,-.7),(3.25,.35),(3.51,.35)],PURPLE)
        joins = VGroup(upper,upper2,lower,lower2,
            Arrow(a.get_right(),b.get_left(),buff=.05,color=PURPLE),
            Arrow(b.get_right(),scale.get_left(),buff=.05,color=PURPLE),
            Arrow(plus.get_right(),output.get_left(),buff=.08,color=GREEN))
        return VGroup(joins,inp,base,a,b,scale,plus,output), base, VGroup(a,b), plus

    def chapter_parallel(self):
        diagram, base, adapters, plus = self.parallel_diagram()
        self.beat(0,reveal=diagram)
        p1,p2=Dot([-5.25,.35,0],.08,color=ORANGE),Dot([-5.25,.35,0],.08,color=ORANGE)
        self.add(p1,p2)
        self.beat(1,animations=[MoveAlongPath(p1,path([(-5.25,.35),(-4.2,.35),(-4.2,1.18),(1.85,1.18),(3.25,1.18),(3.25,.35),(3.8,.35)])),
                               MoveAlongPath(p2,path([(-5.25,.35),(-4.2,.35),(-4.2,-.7),(2.08,-.7),(3.25,-.7),(3.25,.35),(3.8,.35)]))],seconds=4)
        self.remove(p1,p2)
        formula = math(r"y=\operatorname{dequant}(W_4)x+\frac{\alpha}{r}B(Ax)",43).move_to([0,-1.98,0])
        self.beat(2,reveal=formula,animations=[Indicate(plus,color=GREEN)])
        self.beat(3,reveal=self.foot("W₄: 양자화 코드 + 스케일 등 메타데이터"),animations=[Indicate(base,color=BLUE)])

    def chapter_training(self):
        frames=self.sim["frames"]
        base=heatmap(self.sim["base"],BLUE,.31).move_to([-4.9,.7,0])
        b=heatmap(frames[0]["B"],PURPLE,.31).move_to([-2.9,.7,0])
        a=heatmap(frames[0]["A"],GREEN,.31).move_to([-1.2,.7,0])
        self.add(base,b,a,text("W₄ · 고정",22,BLUE).move_to([-4.9,1.7,0]),
            text("B · 학습",22,PURPLE).move_to([-2.9,1.7,0]),text("A · 학습",22,GREEN).move_to([-1.2,1.7,0]))
        self.add(text("4 × 4 선형 층 · r = 2",20,MUTED).move_to([-3.1,-.3,0]))
        ax=Axes(x_range=[0,60,20],y_range=[0,1,.5],x_length=5.4,y_length=2.15,tips=False,
            axis_config={"color":GRID,"stroke_width":2,"include_numbers":False}).move_to([3.2,.65,0])
        self.add(ax,text("정규화 MSE 손실",23,RED).move_to([3.3,2.02,0]),
            text("0",17,MUTED).next_to(ax.c2p(0,0),DOWN,buff=.12),
            text("60 steps",18,MUTED).next_to(ax.c2p(60,0),DOWN,buff=.12),
            text("1.0",17,MUTED).next_to(ax.c2p(0,1),LEFT,buff=.1))
        def curve(n):
            return VMobject(color=RED,stroke_width=4).set_points_as_corners(
                [ax.c2p(f["step"],f["loss"]/frames[0]["loss"]) for f in frames[:n+1]])
        curve_m=curve(1)
        self.add(curve_m)
        arrow=Arrow([-1.0,-.82,0],[-3.4,-.82,0],color=RED,buff=0)
        self.beat(0,reveal=VGroup(arrow,text("loss → gradient",21,RED).move_to([-2.2,-1.15,0])),
            animations=[Indicate(a,color=RED),Indicate(b,color=RED)])
        formulas=math(r"A\leftarrow A-\eta\nabla_A\mathcal L\qquad B\leftarrow B-\eta\nabla_B\mathcal L",33).move_to([0,-1.96,0])
        self.beat(1,reveal=formulas,animations=[Transform(a,heatmap(frames[20]["A"],GREEN,.31).move_to(a)),
            Transform(b,heatmap(frames[20]["B"],PURPLE,.31).move_to(b)),Transform(curve_m,curve(20))],seconds=3)
        freeze=tag("동결 ≠ 기울기 전달 차단",BLUE,23).move_to([3.3,-1.08,0])
        self.beat(2,reveal=freeze,animations=[Indicate(base,color=BLUE)])
        self.beat(3,reveal=self.foot("실제 수치 계산: 작은 선형 회귀 예시 · LLM 성능 벤치마크가 아님"),
            animations=[Transform(a,heatmap(frames[60]["A"],GREEN,.31).move_to(a)),
            Transform(b,heatmap(frames[60]["B"],PURPLE,.31).move_to(b)),Transform(curve_m,curve(60))],seconds=3)

    def chapter_nf4(self):
        ax=Axes(x_range=[-1,1,.5],y_range=[0,1.2,.5],x_length=11.3,y_length=2.3,tips=False,
            axis_config={"color":GRID,"stroke_width":2,"include_ticks":False}).move_to([0,.67,0])
        line_y=ax.c2p(0,0)[1]
        levels=VGroup(*[Dot(ax.c2p(v,0),.061,color=PURPLE) for v in NF4])
        curve=ax.plot(lambda x:np.exp(-.5*(x/.32)**2),x_range=[-1,1],color=BLUE,stroke_width=4)
        self.add(ax,text("−1",20,MUTED).next_to(ax.c2p(-1,0),DOWN,buff=.19),
            text("0",20,MUTED).next_to(ax.c2p(0,0),DOWN,buff=.19),
            text("+1",20,MUTED).next_to(ax.c2p(1,0),DOWN,buff=.19))
        self.beat(0,reveal=levels)
        self.beat(1,reveal=VGroup(curve,text("정규 분포 모양: 설명용",19,MUTED).move_to([3.85,1.75,0])),animations=[Indicate(VGroup(*levels[4:12]),color=PURPLE)])
        vals=np.array([-.81,-.46,-.22,.115,.29,.61])
        targets=NF4[np.abs(vals[:,None]-NF4).argmin(axis=1)]
        dots=VGroup(*[Dot([ax.c2p(v,0)[0],line_y+.35,0],.085,color=ORANGE) for v in vals])
        self.add(dots)
        self.beat(2,reveal=math(r"q=\arg\min_k\left|\frac{w}{s}-c_k\right|",34).move_to([0,-1.5,0]),
            animations=[d.animate.move_to(ax.c2p(v,0)) for d,v in zip(dots,targets)],seconds=3)
        self.beat(3,reveal=VGroup(math(r"\widehat w=s\,c_q\approx w",36).move_to([0,-2.17,0]),
            self.foot("보라: 실제 NF4 코드북 · 주황: 정규화 가중치 예시 · s: 블록 스케일")))

    def chapter_double(self):
        blocks=VGroup(*[card(f"Block {i+1}","4-bit weight codes",BLUE,3.4,1.15) for i in range(3)]).arrange(RIGHT,buff=.65).move_to([0,1.23,0])
        scales=VGroup(*[tag(f"scale s{i+1}",ORANGE,25).move_to([blocks[i].get_x(),-.13,0]) for i in range(3)])
        arrows=VGroup(*[Arrow(blocks[i].get_bottom(),scales[i].get_top(),color=ORANGE,buff=.12) for i in range(3)])
        self.beat(0,reveal=VGroup(blocks,scales,arrows))
        packed=card("Quantized scales", "더 작은 코드 + 상위 스케일",PURPLE,5.2,1.15).move_to([0,-1.43,0])
        self.beat(1,reveal=packed,animations=[TransformFromCopy(scales,tag("scale codes",PURPLE,21).move_to([4.35,-1.43,0]))])
        self.beat(2,reveal=self.foot("압축 대상: 가중치 코드 옆의 스케일 메타데이터",PURPLE),animations=[Indicate(packed,color=PURPLE)])

    def chapter_paging(self):
        gpu=RoundedRectangle(width=5.1,height=2.9,corner_radius=.18,color=BLUE,fill_color=WHITE,fill_opacity=1).move_to([-3.15,.28,0])
        cpu=gpu.copy().set_stroke(MUTED).move_to([3.15,.28,0])
        self.add(gpu,cpu,text("GPU MEMORY",27,BLUE).move_to([-3.15,1.95,0]),text("CPU MEMORY",27,MUTED).move_to([3.15,1.95,0]))
        weights=card("Frozen weights", "기본 모델",BLUE,4.5,.85).move_to([-3.15,.99,0])
        act=card("Activations ↑", "입력 길이 · 배치",ORANGE,4.5,.85).move_to([-3.15,-.02,0])
        pages=VGroup(*[tag(f"state {i+1}",PURPLE,18) for i in range(3)]).arrange(RIGHT,buff=.12).move_to([-3.15,-.86,0])
        self.beat(0,reveal=VGroup(weights,act,pages))
        transfer=DoubleArrow([-.55,-.86,0],[.55,-.86,0],color=PURPLE,buff=0)
        target=pages.copy().move_to([3.15,-.2,0])
        self.beat(1,reveal=transfer,animations=[Transform(pages,target)],seconds=3)
        self.beat(2,reveal=VGroup(tag("메모리 스파이크 관리",GREEN,27).move_to([-3.1,-1.94,0]),
            tag("전송 시간 비용",ORANGE,27).move_to([3.1,-1.94,0]),self.foot("옵티마이저 상태의 이동을 단순화한 개념도 · 실제 VRAM 측정 그래프가 아님")))

    def chapter_memory(self):
        self.add(tag("7B weights · decimal GB",BLUE,23).move_to([0,1.95,0]))
        origin=-3.25
        wide=Rectangle(width=7.8,height=.62,stroke_width=0,fill_color=BLUE,fill_opacity=1).move_to([origin,.85,0],aligned_edge=LEFT)
        small=Rectangle(width=7.8/4,height=.62,stroke_width=0,fill_color=PURPLE,fill_opacity=1).move_to([origin,-.2,0],aligned_edge=LEFT)
        self.add(text("16-bit",27,BLUE).move_to([-4.9,.85,0]),text("4-bit codes",25,PURPLE).move_to([-4.9,-.2,0]))
        labels=VGroup(text("14 GB",29,BLUE).next_to(wide,RIGHT,buff=.2),text("3.5 GB",29,PURPLE).next_to(small,RIGHT,buff=.2))
        self.beat(0,reveal=VGroup(wide,labels),animations=[TransformFromCopy(wide,small)])
        extras=VGroup(*[tag(t,c,23) for t,c in [("스케일 / 비양자화 층",BLUE),("LoRA / 기울기",PURPLE),("옵티마이저 상태",PURPLE)]]).arrange(RIGHT,buff=.3).move_to([0,-1.33,0])
        self.beat(1,reveal=extras)
        self.beat(2,reveal=VGroup(tag("+ 활성값 + 임시 작업 공간",ORANGE,28).move_to([0,-2.12,0]),self.foot("막대는 가중치 표현만 비교 · 총 학습 메모리의 4배 절감을 의미하지 않음")))

    def chapter_recap(self):
        cards=VGroup(card("STORE", "4-bit NF4",BLUE,3.75,1.3),card("COMPUTE", "BF16 / FP16",ORANGE,3.75,1.3),card("UPDATE", "LoRA A, B",PURPLE,3.75,1.3)).arrange(RIGHT,buff=.4).move_to([0,1.36,0])
        self.beat(0,reveal=cards)
        tech=VGroup(tag("NF4",BLUE,24),tag("Double Quantization",PURPLE,24),tag("Paged Optimizer",GREEN,24)).arrange(RIGHT,buff=.35).move_to([0,-.02,0])
        self.beat(1,reveal=tech)
        self.beat(2,reveal=VGroup(text("작업 지시 데이터  →  어댑터 학습  →  평가 / 실행 검증",25,INK,width=12).move_to([0,-1.09,0]),
            self.foot("참고: Dettmers et al., QLoRA (2023) · Hugging Face PEFT")))
        self.beat(3,reveal=math(r"y=\operatorname{dequant}(W_4)x+\frac{\alpha}{r}B(Ax)",43).move_to([0,-2.0,0]),
            animations=[Indicate(cards[0],color=BLUE),Indicate(cards[1],color=ORANGE),Indicate(cards[2],color=PURPLE)])


class QLoRAThumbnail(Scene):
    """Vector thumbnail; no external image assets."""
    def construct(self):
        self.camera.background_color=BG
        self.add(text("LLM FINETUNING  /  VISUAL GUIDE",21,PURPLE).to_corner(UL,buff=.55))
        self.add(text("QLoRA",110,PURPLE).move_to([-3.5,1.28,0]))
        self.add(text("거대한 모델\n작은 업데이트",43,INK).move_to([-3.5,-.37,0]))
        self.add(tag("수식과 애니메이션으로 이해하기",PURPLE,23).move_to([-3.5,-2.04,0]))
        matrix=heatmap(np.random.default_rng(9).uniform(.1,1,(8,8)),BLUE,.27).move_to([3.55,1.08,0])
        self.add(matrix,tag("4-bit · Frozen",BLUE,28).next_to(matrix,UP,buff=.2))
        self.add(text("+",49,INK).move_to([3.55,-.54,0]))
        self.add(card("LoRA A, B", "작은 행렬만 학습",PURPLE,4.75,1.35).move_to([3.55,-1.72,0]))
        self.add(Line([-6.5,-3,0],[6.5,-3,0],color=GRID,stroke_width=2),
                 text("저장은 작게     /     계산은 정밀하게     /     학습은 일부만",27,INK).move_to([0,-3.43,0]))
