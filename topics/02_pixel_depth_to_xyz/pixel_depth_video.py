"""One-file Manim lesson; geometry.py shares the exact camera model with Blender."""
import json
import os
from pathlib import Path
import numpy as np
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.base import SpeechService
from geometry import point, XN, YN

ROOT=Path(__file__).resolve().parent
BG,INK,MUTED,GRID='#F7F9FC','#202D43','#65738A','#DDE5EF'
BLUE,RED,GREEN,ORANGE,PURPLE='#2676D5','#D34F55','#198F70','#ED941D','#8255C7'
FONT='NanumGothic'


def txt(s,size=27,color=INK,width=None):
    m=Text(s,font=FONT,font_size=size,color=color,line_spacing=.8)
    if width and m.width>width:m.scale_to_fit_width(width)
    return m


def eq(s,size=39,width=5.6,color=INK):
    m=MathTex(s,font_size=size,color=color)
    if m.width>width:m.scale_to_fit_width(width)
    return m


def panel(title,sub,color=BLUE,w=5.6,h=1.08):
    return VGroup(RoundedRectangle(width=w,height=h,corner_radius=.13,color=color,
        fill_color=WHITE,fill_opacity=1,stroke_width=1.6),
        txt(title,28,color,w-.3).move_to([0,.18,0]),txt(sub,20,MUTED,w-.3).move_to([0,-.29,0]))


class Speech(SpeechService):
    def __init__(self,records):
        super().__init__(cache_dir=str(ROOT/'assets/audio'))
        self.lookup={r['text']:r for r in records}
    def generate_from_text(self,text,cache_dir=None,path=None,**kwargs):
        return {'input_text':text,'input_data':{'input_text':text,'service':'prepared-pixel-depth'},
                'original_audio':Path(self.lookup[text]['audio']).name}


class PixelDepthLesson(VoiceoverScene):
    def construct(self):
        self.camera.background_color=BG
        self.doc=json.loads((ROOT/'storyboard.json').read_text())
        self.records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
        self.set_speech_service(Speech(self.records),create_subcaption=False)
        self.timeline=[]
        selected=os.environ.get('LESSON_CHAPTER')
        for self.ci,ch in enumerate(self.doc['chapters']):
            if selected and ch['id']!=selected:continue
            self.clear();self.header(ch['title'])
            getattr(self,'chapter_'+ch['id'])()
        name='preview_timeline' if selected else 'render_timeline'
        (ROOT/f'output/{name}.json').write_text(json.dumps(self.timeline,indent=2))

    def header(self,title):
        self.add(txt('CAMERA GEOMETRY  /  PIXEL + DEPTH',16,BLUE).to_corner(UL,buff=.42),
            txt(title,34,width=12.6).move_to([-6.55,3.0,0],aligned_edge=LEFT),
            txt(f'{self.ci+1:02} / 10',18,MUTED).to_corner(UR,buff=.42),
            Line([-6.55,2.5,0],[6.55,2.5,0],color=GRID,stroke_width=2),
            RoundedRectangle(width=6.12,height=4.65,corner_radius=.18,color=GRID,
                stroke_width=1,fill_color=WHITE,fill_opacity=1).move_to([3.25,-.02,0]),
            txt('왜곡 보정 · skew = 0 · 교육용 수치 예시',18,MUTED).move_to([0,-2.83,0]))
        for i in range(10):
            self.add(Line([-6.55+i*1.31,-3.87,0],[-5.38+i*1.31,-3.87,0],
                color=BLUE if i<=self.ci else GRID,stroke_width=5))

    def item(self,s,y,math=False,size=32,color=INK):
        m=eq(s,size,color=color) if math else txt(s,size,color,width=5.55)
        return m.move_to([3.25,y,0])

    def beat(self,li,reveal=None,motion=None):
        r=next(r for r in self.records if r['chapter']==self.ci and r['line']==li)
        start=self.time
        with self.voiceover(text=r['text']):
            rem=r['duration']
            if reveal is not None:
                self.play(FadeIn(reveal,shift=UP*.05),run_time=.6);rem-=.6
            elif motion:
                self.wait(.6+1e-7,frozen_frame=True);rem-=.6
            if motion:
                self.play(*motion,run_time=3.-1e-7,rate_func=lambda s:s*s*(3-2*s));rem-=3.
            if rem>1/30:self.wait(round(rem,9)+1e-7,frozen_frame=True)
        self.timeline.append(dict(chapter=self.ci,line=li,start=start,end=self.time))

    def p(self,x,y,z):
        return np.array([-5.85,.65,0])+x*np.array([1.15,.6,0])+y*np.array([.48,-1.15,0])+z*np.array([1.62,-.49,0])

    def geometry(self,z=2,range_label=False):
        o=self.p(0,0,0);p=self.p(*point(z));q=self.p(0,0,z)
        g=VGroup()
        for end,col,label in [((.9,0,0),RED,'X'),((0,.85,0),GREEN,'Y'),((0,0,2.7),BLUE,'Z')]:
            target=self.p(*end);g.add(Arrow(o,target,buff=0,color=col,stroke_width=3),txt(label,22,col).next_to(target,RIGHT,buff=.07))
        corners=[self.p(x,y,.75) for x,y in [(-.4,-.3),(.4,-.3),(.4,.3),(-.4,.3)]]
        g.add(Polygon(*corners,color=BLUE,fill_color=BLUE,fill_opacity=.08,stroke_width=2))
        for c in corners:g.add(Line(o,c,color=GRID,stroke_width=1.4))
        g.add(Line(o,self.p(*point(2.7)),color=ORANGE,stroke_width=3),Dot(o,.085,color=INK),
              Dot(self.p(*point(.75)),.065,color=ORANGE),Dot(p,.105,color=ORANGE),
              DashedLine(q,p,color=RED,stroke_width=2),
              txt('C',22,INK).next_to(o,UL,buff=.08),txt('P',26,ORANGE).next_to(p,UP,buff=.12),
              txt('pixel',20,ORANGE).move_to([-4.45,1.45,0]))
        plane=[self.p(x,y,z) for x,y in [(-.55,-.4),(.55,-.4),(.55,.4),(-.55,.4)]]
        g.add(Polygon(*plane,color=BLUE,stroke_width=1.5,fill_color=BLUE,fill_opacity=.045))
        g.add(txt(f'Z = {z:.2f} m',25,BLUE).move_to([-3.5,-1.85,0]))
        if range_label:g.add(txt(f'R = {np.linalg.norm(point(z)):.3f} m',24,ORANGE).move_to([-3.5,-2.28,0]))
        return g

    def rig(self,z=2,range_label=False):
        self.z=ValueTracker(z)
        self.drawing=always_redraw(lambda:self.geometry(self.z.get_value(),range_label))
        self.add(self.drawing,txt('CAMERA → PIXEL → RAY → POINT',18,MUTED).move_to([-3.55,2.13,0]))

    def pixels(self):
        center=np.array([-3.5,-.1,0]);w,h=5.35,4.0125
        def pixel(u,v):return center+np.array([(u-320)/640*w,-(v-240)/480*h,0])
        rect=Rectangle(width=w,height=h,color=GRID,fill_color=WHITE,fill_opacity=1)
        rect.move_to(center);g=VGroup(rect)
        for u in range(0,641,80):g.add(Line(pixel(u,0),pixel(u,480),color=GRID,stroke_width=1))
        for v in range(0,481,80):g.add(Line(pixel(0,v),pixel(640,v),color=GRID,stroke_width=1))
        g.add(Arrow(pixel(0,0),pixel(640,0),color=INK,buff=0),Arrow(pixel(0,0),pixel(0,480),color=INK,buff=0),
            txt('u [px]',20).next_to(pixel(640,0),DOWN,buff=.1),txt('v [px]',20).next_to(pixel(0,480),RIGHT,buff=.1),
            Dot(pixel(320,240),.07,color=BLUE),txt('(cx, cy)',23,BLUE).next_to(pixel(320,240),UL,buff=.1),
            Dot(pixel(440,300),.09,color=ORANGE),txt('(u, v)',23,ORANGE).next_to(pixel(440,300),DR,buff=.1))
        self.add(g)
        return pixel

    def chapter_hook(self):
        self.rig(2)
        self.beat(0,self.item('픽셀만으로는\n거리를 알 수 없다',1.1,size=34))
        self.z.set_value(1)
        self.beat(1,self.item('같은 픽셀 = 같은 광선',-.15,size=29,color=ORANGE),[self.z.animate.set_value(2.5)])
        self.beat(2,self.item('Pixel + Depth → 3D',-1.4,size=31,color=BLUE),[self.z.animate.set_value(2)])

    def chapter_frames(self):
        self.rig()
        self.beat(0,self.item('u → 오른쪽   v → 아래쪽',1.45,size=27))
        self.beat(1,VGroup(self.item('X 오른쪽',.45,size=29,color=RED),self.item('Y 아래쪽',-.2,size=29,color=GREEN),self.item('Z 전방',-.85,size=29,color=BLUE)))
        self.beat(2,self.item('픽셀: px   /   공간: m',-1.7,size=27))

    def chapter_intrinsics(self):
        pixel=self.pixels()
        self.beat(0,self.item(r'f_x,\ f_y,\ c_x,\ c_y',1.45,True,43))
        self.beat(1,self.item('주점은 보정으로 결정',.35,size=30,color=BLUE))
        offsets=VGroup(DashedLine(pixel(320,240),pixel(440,240),color=ORANGE),DashedLine(pixel(440,240),pixel(440,300),color=ORANGE))
        self.beat(2,VGroup(offsets,self.item(r'x_n=\frac{u-c_x}{f_x}',-.6,True,41),self.item(r'y_n=\frac{v-c_y}{f_y}',-1.65,True,41)))

    def chapter_ray(self):
        self.rig(1)
        self.beat(0,self.item(r'\mathbf d=(x_n,y_n,1)^T',1.3,True,42))
        self.beat(1,VGroup(self.item(r'\|\mathbf d\|=\sqrt{x_n^2+y_n^2+1}',.12,True,33),self.item('Z 성분이 1인 방향 벡터',-.5,size=24,color=MUTED)))
        self.beat(2,self.item(r'\mathbf P=Z\mathbf d',-1.55,True,48),[self.z.animate.set_value(2)])

    def chapter_formula(self):
        o=np.array([-6.1,-1.1,0]);p=o+np.array([4.8,2.5,0]);q=o+np.array([4.8,0,0]);a=o+np.array([1.9,0,0]);b=o+(p-o)*(1.9/4.8)
        self.add(Polygon(o,q,p,color=BLUE,fill_color=BLUE,fill_opacity=.05),Polygon(o,a,b,color=ORANGE,fill_color=ORANGE,fill_opacity=.13),
            txt('Z',26,BLUE).next_to(Line(o,q),DOWN,buff=.15),txt('X',26,RED).next_to(Line(q,p),RIGHT,buff=.12),
            txt('X–Z 단면 · 삼각형의 닮음',22,MUTED).move_to([-3.65,2.05,0]),
            txt('정규화 영상 평면',21,ORANGE).move_to([-4.55,-2.1,0]))
        self.beat(0,self.item(r'\frac XZ=\frac{u-c_x}{f_x}',1.35,True,45))
        self.beat(1,self.item(r'X=\frac{(u-c_x)Z}{f_x}',-.02,True,45,color=RED))
        self.beat(2,self.item(r'Y=\frac{(v-c_y)Z}{f_y}',-1.4,True,45,color=GREEN))

    def chapter_matrix(self):
        k=eq(r'K=\begin{bmatrix}f_x&0&c_x\\0&f_y&c_y\\0&0&1\end{bmatrix}',45).move_to([-3.5,.7,0])
        self.beat(0,VGroup(k,txt('카메라 내부 행렬',28,BLUE).move_to([-3.5,1.95,0]),self.item('초점 거리: fx, fy [px]',1.3,size=28)))
        self.beat(1,VGroup(eq(r'\mathbf P=ZK^{-1}\begin{bmatrix}u\\v\\1\end{bmatrix}',42).move_to([-3.5,-1.32,0]),self.item('주점: (cx, cy) [px]',.1,size=28)))
        self.beat(2,self.item('보정된 픽셀\n+ 그 영상에 맞는 K',-1.3,size=29,color=PURPLE))

    def chapter_example(self):
        self.rig()
        self.beat(0,VGroup(self.item(r'f_x=f_y=600\ \mathrm{px}',1.55,True,34),self.item(r'(c_x,c_y)=(320,240)',.85,True,33)))
        self.beat(1,VGroup(self.item(r'(u,v)=(440,300),\ Z=2\ \mathrm m',-.02,True,31),self.item(r'X=\frac{120\times2}{600}=0.4\ \mathrm m',-.8,True,32)))
        self.beat(2,VGroup(self.item(r'Y=\frac{60\times2}{600}=0.2\ \mathrm m',-1.55,True,32),txt('P = (0.4, 0.2, 2.0) m',27,ORANGE).move_to([-3.5,-2.32,0])))

    def chapter_depth_range(self):
        self.rig(range_label=True)
        self.beat(0,self.item('광학축 깊이 Z ≠ 직선거리 R',1.45,size=28,color=BLUE))
        self.beat(1,VGroup(self.item(r'R=\sqrt{X^2+Y^2+Z^2}',.4,True,36),self.item(r'R\approx2.049\ \mathrm m',-.37,True,36,color=ORANGE)))
        self.beat(2,self.item(r'Z=\frac{R}{\sqrt{x_n^2+y_n^2+1}}',-1.6,True,39))

    def chapter_quality(self):
        left=VGroup(panel('RGB pixel','물체가 검출된 영상',BLUE),panel('Aligned depth','같은 픽셀의 광학축 깊이 Z',PURPLE),panel('Matching K','그 영상에 대응하는 내부 파라미터',GREEN)).arrange(DOWN,buff=.42).move_to([-3.5,.03,0])
        self.beat(0,VGroup(left,self.item('같은 픽셀 번호라도\n같은 방향은 아닐 수 있다',1.2,size=29)))
        self.beat(1,self.item('정렬된 깊이 + 대응 K',-.2,size=29,color=BLUE))
        self.beat(2,VGroup(self.item('단위 변환 · 무효 값 제외',-1.1,size=27,color=PURPLE),self.item('1000 mm = 1 m',-1.8,size=27)))

    def chapter_robot(self):
        self.rig()
        self.beat(0,VGroup(self.item(r'\mathbf P_b=R_{bc}\mathbf P_c+\mathbf t_{bc}',1.15,True,36),self.item('카메라 → 로봇 베이스',.5,size=26,color=BLUE)))
        self.beat(1,VGroup(self.item('pixel + K → ray',-.35,size=29,color=ORANGE),self.item('ray + Z → 3D point',-1.07,size=29,color=BLUE)))
        self.beat(2,self.item(r'Z=1\Rightarrow\mathbf P=(0.2,0.1,1)',-1.8,True,29),[self.z.animate.set_value(1)])
