"""Manim dashboard driven entirely by the measured Blender trace, at 30 fps."""
import json
from pathlib import Path
import numpy as np
from manim import *

ROOT=Path(__file__).resolve().parent
BG,INK,MUTED,GRID='#F7F9FC','#202D43','#65738A','#DDE5EF'
BLUE,GREEN,RED,ORANGE='#2676D5','#198F70','#D34F55','#ED941D'


def screen(x,y):return np.array([(x-960)/135,(540-y)/135,0])


def txt(s,size=22,color=INK):return Text(s,font='NanumGothic',font_size=size,color=color)


def put(m,x,y):return m.move_to(screen(x,y))


class ObservationDashboard(Scene):
    def construct(self):
        self.camera.background_color=BG
        self.trace=json.loads((ROOT/'output/trace.json').read_text())
        self.doc=json.loads((ROOT/'storyboard.json').read_text())
        self.records=json.loads((ROOT/'assets/audio/manifest.json').read_text())
        self.add_sound(str(ROOT/'output/narration.wav'))
        self.timeline=[]
        for ci,ch in enumerate(self.doc['chapters']):
            records=[r for r in self.records if r['chapter']==ci]
            start,end=round(records[0]['start']*30),round(records[-1]['end']*30)
            self.clear();self.ci=ci;self.counter=ValueTracker(start)
            self.build(ch['title'])
            driver=VectorizedPoint();driver.add_updater(lambda _:self.refresh())
            self.add(driver);self.refresh()
            moving=min(end-start,331) if ci<7 else 0
            actual_start=self.time
            if moving:
                self.play(self.counter.animate.set_value(start+moving),run_time=moving/30-1e-7,rate_func=linear)
            if end-start-moving:
                self.wait((end-start-moving)/30+1e-7,frozen_frame=True)
            driver.clear_updaters()
            self.timeline.append(dict(chapter=ci,start=actual_start,end=self.time,frame_start=start,frame_end=end))
        (ROOT/'output/dashboard_timeline.json').write_text(json.dumps(self.timeline,indent=2))

    def build(self,title):
        self.add(put(txt('CAMERA OBSERVATION / RECONSTRUCTION EXPERIMENT',17,BLUE),515,65),
            put(txt(f'{self.ci+1:02} / 08',18,MUTED),1780,65))
        heading=txt(title,36)
        if heading.width>12.9:heading.scale_to_fit_width(12.9)
        self.add(heading.move_to(screen(65,136),aligned_edge=LEFT),Line(screen(60,192),screen(1840,192),color=GRID,stroke_width=2))
        for x,y,w,h in [(460,520,860,580),(1150,422,440,345),(1610,422,440,345)]:
            self.add(put(RoundedRectangle(width=w/135,height=h/135,corner_radius=.12,stroke_color=GRID,stroke_width=1,fill_color=WHITE,fill_opacity=1),x,y))
        self.add(put(txt('3D 장면',23),140,218),put(txt('● 실제 표면',20,GREEN),370,218),put(txt('○ 복원 위치',20,RED),605,218),
            put(txt('카메라 RGB · 160×120',23),1150,218),put(txt('관측 깊이 Z [m]',23),1610,218))
        # The image overlays end at y=590; this legend remains visible below them.
        stops=['#385AAF','#25BED0','#F2D24A','#E67B32']
        colors=color_gradient(stops,80)
        bar=VGroup(*[Rectangle(width=4.9/135,height=10/135,stroke_width=0,fill_color=c,fill_opacity=1) for c in colors]).arrange(RIGHT,buff=0)
        self.add(put(bar,1610,608),put(txt('1.0',13,MUTED),1415,627),put(txt('4.5 m',13,MUTED),1788,627))
        self.add(put(txt('관측 (u,v) =',21),145,851),put(txt('Z =',21),495,851),put(txt('m',19,MUTED),705,851),
            put(txt('GT 표면 P =',21,GREEN),151,894),put(txt('복원 P =',21,RED),130,935))
        self.values={}
        for key,x,y,dec,col in [('u',280,851,0,INK),('v',360,851,0,INK),('z',597,851,4,INK),
            ('tx',323,894,4,GREEN),('ty',509,894,4,GREEN),('tz',695,894,4,GREEN),
            ('ex',323,935,4,RED),('ey',509,935,4,RED),('ez',695,935,4,RED)]:
            value=DecimalNumber(0,num_decimal_places=dec,font_size=23,color=col,group_with_commas=False)
            put(value,x,y);self.values[key]=(value,x,y);self.add(value)
        self.add(put(txt('m',18,MUTED),815,894),put(txt('m',18,MUTED),815,935))
        formula=MathTex(r'X=\frac{(u-c_x)Z}{f_x}\qquad Y=\frac{(v-c_y)Z}{f_y}',font_size=34,color=INK)
        if formula.width>6.4:formula.scale_to_fit_width(6.4)
        self.add(put(formula,1400,887),put(txt('fx 실제 = 150 px  /  fx 복원 =',18,MUTED),1270,943))
        value=DecimalNumber(150,num_decimal_places=0,font_size=21,color=RED,group_with_commas=False);put(value,1640,943);self.values['fx']=(value,1640,943);self.add(value)
        self.add(put(txt('px',17,MUTED),1710,943))
        self.add(put(txt('실험 시간',18,MUTED),620,795),put(txt('/ 10.0 s',17,MUTED),804,795))
        value=DecimalNumber(0,num_decimal_places=2,font_size=19,color=INK);put(value,720,795);self.values['time']=(value,720,795);self.add(value)
        if self.ci>=6:
            self.add(put(txt('동일 경로 · 301개 표본의 RMSE [mm]',21),1390,665))
            for i,(mode,name,c) in enumerate([('ideal','기준',GREEN),('noise','깊이 잡음',ORANGE),('bad_k','잘못된 fx',RED),('correct','보정 복구',BLUE)]):
                x=1020+i*245
                self.add(put(txt(name,20,c),x,715),put(txt(f"{self.trace['metrics'][mode]['rmse_mm']:.3f}",31,c),x,763))
            self.curve=None
        else:
            if self.ci<=1:self.plot_key='estimated';self.component=0;yr=[-.6,.6,.3];label='복원 X [m]';color=BLUE
            elif self.ci==2:self.plot_key='z_observed';self.component=None;yr=[0,4.5,1.5];label='관측 Z [m]';color=BLUE
            else:self.plot_key='error_mm';self.component=None;yr=[0,150,50];label='3D 위치 오차 [mm]';color=GREEN if self.ci==3 else (ORANGE if self.ci==4 else RED)
            self.plot_color=color
            self.ax=Axes(x_range=[0,10,5],y_range=yr,x_length=810/135,y_length=135/135,tips=False,axis_config={'color':GRID,'stroke_width':1.5,'include_ticks':True,'tick_size':.03})
            put(self.ax,1410,722)
            self.add(self.ax,put(txt(label,19,color),1080,642))
            for t in [0,5,10]:self.add(txt(str(t),13,MUTED).next_to(self.ax.c2p(t,yr[0]),DOWN,buff=.05))
            for val in [yr[0],yr[-1]]:self.add(txt(f'{val:g}',13,MUTED).next_to(self.ax.c2p(0,val),LEFT,buff=.08))
            self.add(put(txt('실험 시간 [s]',13,MUTED),1770,812))
            self.curve=VMobject(color=color,stroke_width=3);self.add(self.curve)
            self.add(put(txt('현재 오차',17,MUTED),1475,642),put(txt('mm',16,MUTED),1810,642))
            val=DecimalNumber(0,num_decimal_places=2,font_size=23,color=color);put(val,1675,642);self.values['error']=(val,1675,642);self.add(val)
        for i in range(8):self.add(Line(screen(60+i*222,1060),screen(262+i*222,1060),color=BLUE if i<=self.ci else GRID,stroke_width=5))

    def refresh(self):
        frame=min(len(self.trace['video_map'])-1,max(0,int(round(self.counter.get_value()))))
        st=self.trace['states'][self.trace['video_map'][frame]]
        values=dict(u=st['uv'][0],v=st['uv'][1],z=st['z_observed'],fx=st['fx_used'],time=st['sim_time'],error=st['error_mm'],
            tx=st['true_surface'][0],ty=st['true_surface'][1],tz=st['true_surface'][2],
            ex=st['estimated'][0],ey=st['estimated'][1],ez=st['estimated'][2])
        for key,(m,x,y) in self.values.items():m.set_value(values[key]);put(m,x,y)
        if self.curve is not None:
            ids=self.trace['phase_states'][self.ci][:st['sample']+1]
            points=[]
            for sid in ids:
                item=self.trace['states'][sid];value=item[self.plot_key]
                if self.component is not None:value=value[self.component]
                points.append(self.ax.c2p(item['sim_time'],value))
            if len(points)==1:points*=2
            self.curve.set_points_as_corners(points)
