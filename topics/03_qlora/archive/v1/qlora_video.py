"""Manim CE animation explaining QLoRA. No external images are required."""
from manim import *
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BG, INK, MUTED = "#F7F9FC", "#202D43", "#65738A"
BLUE, PURPLE, GREEN, ORANGE, RED, GRID = "#2676D5", "#8255C7", "#198F70", "#ED941D", "#D34F55", "#DDE5EF"
FONT = "NanumGothic"
SCENE_SECONDS = 18

def txt(s, size=30, color=INK, **kw): return Text(s, font=FONT, font_size=size, color=color, **kw)
def eq(s, size=38): return MathTex(s, font_size=size, color=INK)
def box(title, sub, color, w=3.0, h=1.25):
    r=RoundedRectangle(width=w,height=h,corner_radius=.14,stroke_color=color,stroke_width=3,fill_color=WHITE,fill_opacity=1)
    return VGroup(r,txt(title,27,color).move_to(r.get_center()+UP*.18),txt(sub,18,MUTED).move_to(r.get_center()+DOWN*.28))
def arrow_between(a,b,color=MUTED): return Arrow(a.get_right(),b.get_left(),buff=.12,color=color,stroke_width=4)

class QLoRALesson(Scene):
    def construct(self):
        self.camera.background_color=BG
        self.chapters=[]
        for i,fn in enumerate([self.problem,self.lora,self.qlora,self.backward,self.three_tricks,self.memory,self.recipe,self.recap]):
            self.clear(); self.header(i); start=self.time; fn(); self.wait(max(0,SCENE_SECONDS-(self.time-start)))
            self.chapters.append({"index":i,"start":start,"end":self.time})
        (ROOT/'output').mkdir(exist_ok=True)
        (ROOT/'output/timeline.json').write_text(json.dumps(self.chapters,indent=2))

    def header(self,i):
        titles=["왜 전체 파인튜닝은 무거울까?","LoRA: 작은 우회 경로만 학습","QLoRA: Q + LoRA","역전파는 어디로 흐를까?","QLoRA의 세 가지 메모리 장치","메모리는 얼마나 줄어들까?","실제 학습 설정의 핵심","QLoRA를 한 장으로 정리"]
        self.add(txt("LLM TRAINING / QLoRA",16,BLUE).to_corner(UL,buff=.4),txt(titles[i],38).move_to([-1.1,3.0,0]),txt(f"{i+1:02d} / 08",18,MUTED).to_corner(UR,buff=.4))
        self.add(Line([-6.7,2.52,0],[6.7,2.52,0],color=GRID),Line([-7.1,-3.95,0],[-7.1+14.2*(i+1)/8,-3.95,0],color=BLUE,stroke_width=6))
        self.add(txt("교육용 개념도 · 메모리 수치는 weight-only 예시",15,MUTED).move_to([0,-3.55,0]))

    def problem(self):
        model=box("Pretrained LLM","수십억 개의 parameter",PURPLE,4.1,1.45).move_to([0,1.25,0])
        self.play(FadeIn(model,shift=UP*.2),run_time=1.2)
        rows=VGroup(*[box(a,b,c,3.25,1.15) for a,b,c in [("Weights","모든 W 업데이트",PURPLE),("Gradients","모든 ∇W 저장",RED),("Optimizer states","momentum / variance",ORANGE)]]).arrange(RIGHT,buff=.5).move_to([0,-.55,0])
        self.play(LaggedStart(*[FadeIn(x,shift=UP*.1) for x in rows],lag_ratio=.25),run_time=2.3)
        brace=Brace(rows,DOWN,color=RED); warning=txt("학습 메모리가 크게 증가",31,RED).next_to(brace,DOWN,.18)
        self.play(GrowFromCenter(brace),Write(warning),run_time=1.5)
        self.wait(2); self.play(Indicate(model,color=ORANGE),run_time=1.5)
        note=txt("질문: 모든 W를 바꿔야 할까?",34,GREEN).move_to([0,-2.55,0]); self.play(ReplacementTransform(warning,note),run_time=1.4)

    def lora(self):
        formula=eq(r"\mathbf y=(\mathbf W+\Delta\mathbf W)\mathbf x,\qquad \Delta\mathbf W={\alpha\over r}\mathbf B\mathbf A",40).move_to([0,1.75,0])
        self.play(Write(formula),run_time=2)
        W=Rectangle(width=3.2,height=2.2,color=MUTED,fill_color="#E5EAF1",fill_opacity=1).move_to([-3.6,-.25,0])
        A=Rectangle(width=2.2,height=.42,color=GREEN,fill_color=GREEN,fill_opacity=.35).move_to([.1,.1,0])
        B=Rectangle(width=.42,height=2.2,color=GREEN,fill_color=GREEN,fill_opacity=.35).move_to([1.6,-.8,0])
        self.play(FadeIn(W),FadeIn(A),FadeIn(B),run_time=1.5)
        self.add(txt("W: frozen",24,MUTED).move_to(W),txt("A: r × din",21,GREEN).next_to(A,UP,.1),txt("B: dout × r",21,GREEN).next_to(B,RIGHT,.1))
        rank=txt("r ≪ min(din, dout)",28,GREEN).move_to([3.75,.3,0]); self.play(Write(rank),run_time=1.3)
        counts=eq(r"d_{out}d_{in}\quad\longrightarrow\quad r(d_{in}+d_{out})",34).move_to([2.6,-2.1,0]);self.play(Write(counts),run_time=1.6)
        self.wait(2);self.play(Indicate(VGroup(A,B),color=ORANGE),run_time=1.5)

    def qlora(self):
        full=box("16-bit base weights","큰 저장 공간",PURPLE,3.5,1.4).move_to([-3.5,1.2,0])
        q=box("NF4 4-bit weights","저장 · frozen",BLUE,3.5,1.4).move_to([0,1.2,0])
        deq=box("Dequantize","BF16 compute",ORANGE,3.2,1.4).move_to([3.6,1.2,0])
        self.play(FadeIn(full),run_time=1); self.play(TransformFromCopy(full,q),run_time=1.6);self.play(GrowArrow(arrow_between(q,deq)),FadeIn(deq),run_time=1.5)
        base=box("Frozen base path",r"dequant(W₄) x",BLUE,4.0,1.35).move_to([-2.5,-.65,0])
        adapter=box("Trainable LoRA path",r"(α/r) B A x",GREEN,4.0,1.35).move_to([2.5,-.65,0])
        self.play(FadeIn(base),FadeIn(adapter),run_time=1.5)
        sum_eq=eq(r"\mathbf y=\operatorname{dequant}(\mathbf W_4)\mathbf x+{\alpha\over r}\mathbf B\mathbf A\mathbf x",36).move_to([0,-2.25,0])
        self.play(Write(sum_eq),run_time=2)
        self.play(FadeOut(full),q.animate.move_to([-1.7,1.2,0]),deq.animate.move_to([1.7,1.2,0]),run_time=1.2)
        self.wait(1.5)

    def backward(self):
        x=box("Input x","BF16 / FP16",ORANGE,2.4,1.1).move_to([-5,1.25,0]);w=box("W₄","4-bit · frozen",BLUE,2.4,1.1).move_to([-1.8,1.25,0]);ab=box("A, B","trainable",GREEN,2.4,1.1).move_to([1.5,1.25,0]);loss=box("Loss","task objective",RED,2.4,1.1).move_to([4.8,1.25,0])
        flow=VGroup(x,w,ab,loss,arrow_between(x,w),arrow_between(w,ab),arrow_between(ab,loss))
        self.play(LaggedStart(*[FadeIn(m) for m in flow],lag_ratio=.12),run_time=2.5)
        grad=CurvedArrow(loss.get_bottom(),ab.get_bottom(),angle=-TAU/5,color=RED,stroke_width=5)
        passthrough=CurvedArrow(ab.get_bottom(),w.get_bottom(),angle=-TAU/5,color=RED,stroke_width=4)
        self.play(Create(grad),Create(passthrough),run_time=1.8)
        self.add(txt("gradient",21,RED).next_to(grad,DOWN,.08))
        frozen=VGroup(txt("W₄ update",26,MUTED),Cross(stroke_color=RED,stroke_width=5)).arrange(RIGHT).move_to([-2,-1.4,0])
        trained=VGroup(txt("A, B update",27,GREEN),txt("✓",32,GREEN)).arrange(RIGHT).move_to([2,-1.4,0])
        self.play(FadeIn(frozen),FadeIn(trained),run_time=1.5)
        note=txt("optimizer state도 adapter parameter에만 필요",29,INK).move_to([0,-2.55,0]);self.play(Write(note),run_time=1.6);self.wait(2)

    def three_tricks(self):
        cards=VGroup(box("1  NF4","normal-distributed weight용 4-bit",BLUE,3.8,2.15),box("2  Double Quant","quantization constant도 양자화",PURPLE,3.8,2.15),box("3  Paged Optimizer","메모리 spike를 page로 관리",ORANGE,3.8,2.15)).arrange(RIGHT,buff=.35).move_to([0,.5,0])
        self.play(LaggedStart(*[FadeIn(c,shift=UP*.2) for c in cards],lag_ratio=.3),run_time=3)
        dots=VGroup(*[Dot([-.7+i*.2,-.1,0],radius=.04,color=BLUE) for i in [-4,-2,-1,0,1,2,4]])
        dots.move_to(cards[0][0].get_center()+DOWN*.68);self.play(FadeIn(dots),run_time=1)
        scales=VGroup(*[Square(.22,color=PURPLE,fill_color=PURPLE,fill_opacity=.35) for _ in range(6)]).arrange(RIGHT,.08).move_to(cards[1][0].get_center()+DOWN*.68);self.play(FadeIn(scales),run_time=1)
        page=VGroup(*[RoundedRectangle(width=.45,height=.28,corner_radius=.04,color=ORANGE) for _ in range(6)]).arrange_in_grid(2,3,buff=.08).move_to(cards[2][0].get_center()+DOWN*.68);self.play(FadeIn(page),run_time=1)
        note=txt("세 장치는 서로 다른 메모리 문제를 해결",31,GREEN).move_to([0,-2.1,0]);self.play(Write(note),run_time=1.6);self.wait(2)

    def memory(self):
        title=txt("7B parameter · weight storage only (illustrative)",25,MUTED).move_to([0,1.9,0]);self.play(FadeIn(title))
        left=Rectangle(width=5.6,height=1.15,color=PURPLE,fill_color=PURPLE,fill_opacity=.4).move_to([-2.65,.75,0])
        right=Rectangle(width=1.4,height=1.15,color=BLUE,fill_color=BLUE,fill_opacity=.55).move_to([-4.75,-.8,0])
        self.play(GrowFromEdge(left,LEFT),run_time=1.4);self.add(txt("FP16/BF16 weights ≈ 14 GB",29).move_to(left))
        self.play(GrowFromEdge(right,LEFT),run_time=1.4);self.add(txt("4-bit\n≈ 3.5 GB",19,WHITE,line_spacing=.8).move_to(right))
        ratio=eq(r"7\times10^9\times {16\over8}\approx14\,GB\qquad 7\times10^9\times {4\over8}\approx3.5\,GB",31).move_to([1.7,-.8,0]);self.play(Write(ratio),run_time=2)
        extras=txt("실제 학습 = weights + activations + LoRA + optimizer + workspace",27,RED).move_to([0,-2.2,0]);self.play(Write(extras),run_time=1.8)
        self.wait(2);self.play(Indicate(extras,color=ORANGE),run_time=1.5)

    def recipe(self):
        code=Code(code_string='''bnb = BitsAndBytesConfig(\n  load_in_4bit=True,\n  bnb_4bit_quant_type="nf4",\n  bnb_4bit_use_double_quant=True,\n  bnb_4bit_compute_dtype=torch.bfloat16\n)\nmodel = prepare_model_for_kbit_training(model)\nlora = LoraConfig(r=16, target_modules="all-linear")''',language="python",background="window",paragraph_config={"font_size":21}).scale(.87).move_to([-2.6,-.1,0])
        self.play(FadeIn(code),run_time=2)
        steps=VGroup(*[box(a,b,c,4.1,1.05) for a,b,c in [("Load 4-bit","NF4 + double quant",BLUE),("Prepare","k-bit training",ORANGE),("Attach LoRA","all linear layers",GREEN)]]).arrange(DOWN,buff=.35).move_to([3.65,.2,0])
        self.play(LaggedStart(*[FadeIn(s,shift=LEFT*.15) for s in steps],lag_ratio=.3),run_time=2.4)
        caution=txt("compute dtype ≠ storage dtype",27,RED).move_to([3.65,-2.35,0]);self.play(Write(caution),run_time=1.4);self.wait(2)

    def recap(self):
        data=box("Dataset","instruction / domain data",ORANGE,2.6,1.2).move_to([-5,1.0,0]);base=box("Frozen W₄","NF4 4-bit base",BLUE,2.6,1.2).move_to([-1.7,1,0]);adapter=box("Train A, B","small LoRA adapter",GREEN,2.6,1.2).move_to([1.7,1,0]);out=box("Adapter","task checkpoint",PURPLE,2.6,1.2).move_to([5,1,0])
        flow=VGroup(data,base,adapter,out,arrow_between(data,base),arrow_between(base,adapter),arrow_between(adapter,out));self.play(LaggedStart(*[FadeIn(x) for x in flow],lag_ratio=.1),run_time=3)
        formula=eq(r"\underbrace{\mathbf W_4}_{\text{frozen}}+\underbrace{{\alpha\over r}\mathbf B\mathbf A}_{\text{trainable}}",42).move_to([0,-.75,0]);self.play(Write(formula),run_time=2)
        recap=VGroup(txt("4-bit storage",27,BLUE),txt("+ low-rank update",27,GREEN),txt("= memory-efficient fine-tuning",27,PURPLE)).arrange(RIGHT,buff=.25).move_to([0,-2.1,0]);self.play(LaggedStart(*[FadeIn(x,shift=UP*.1) for x in recap],lag_ratio=.25),run_time=1.8);self.wait(2)
