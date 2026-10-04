from pathlib import Path
import json, numpy as np
from manim import *
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'output/trace.json').read_text())
A=json.loads((ROOT/'assets/audio/manifest.json').read_text())
ST=json.loads((ROOT/'storyboard.json').read_text())
BG='#F7F9FC';INK='#233247';BLUE='#147DAD';ORANGE='#DC781A';GREEN='#198465';MUTED='#718096'
def txt(s,size=28,color=INK):return Text(s,font='NanumGothic',font_size=size,color=color)
def R(a):return np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
def trans(points,p):return np.array(points)@R(p[2]).T+np.array(p[:2])
def pos(p):return np.array([p[0]*.67-2.1,p[1]*.67-.15,0])
def cloud(points,color):return VGroup(*[Dot(pos(p),radius=.024,color=color) for p in points])
def robot(p,color=BLUE):
    c=pos(p);body=RoundedRectangle(width=.45,height=.35,corner_radius=.08,color=color,fill_opacity=1).move_to(c)
    arrow=Arrow(c,c+np.array([np.cos(p[2]),np.sin(p[2]),0])*.43,buff=0,color=color,stroke_width=4)
    return VGroup(body,arrow)
def grid_image(log):
    log=np.array(log);arr=np.zeros((*log.shape,3),np.uint8);arr[:]=[196,204,213];arr[log<-.15]=[250,252,255];arr[log>.2]=[24,113,153]
    return ImageMobject(arr[::-1]).set_resampling_algorithm(RESAMPLING_ALGORITHMS['nearest']).set(width=6.0).move_to([-2,.0,0])
class SlamLesson(Scene):
    def construct(self):
        self.camera.background_color=BG
        for ci,ch in enumerate(ST['chapters']):
            if hasattr(self,'only_chapter') and ci!=self.only_chapter:continue
            self.clear();self.add(txt(f'{ci+1:02d} / 08   SLAM',20,MUTED).to_corner(UL,buff=.35))
            self.add(txt(ch['title'],36).move_to([0,3.05,0]))
            self.add(Line([-6.6,2.57,0],[6.6,2.57,0],color='#DCE4ED'))
            self.add(txt('교육용 2D 모의 관측 · m / rad',16,MUTED).move_to([0,-2.82,0]))
            subtitle=None
            def say(li,anim=None,run=2):
                nonlocal subtitle
                rec=next(r for r in A if r['chapter']==ci and r['line']==li)
                if subtitle:self.remove(subtitle)
                subtitle=txt(rec['caption'],26).move_to([0,-3.43,0]);self.add(subtitle)
                if anim:self.play(anim,run_time=min(run,rec['duration']-.2));self.wait(max(.01,rec['duration']-run))
                else:self.wait(rec['duration'])
            def side(lines):
                v=VGroup(*[txt(s,25) for s in lines]).arrange(DOWN,buff=.42).move_to([4.45,.2,0]);self.add(v);return v
            if ci==0:
                side(['Map = ?','Robot Pose = ?','관측 + 이동','↓','위치 + 지도'])
                for i in range(3):say(i)
            elif ci==1:
                side(['360° LiDAR','↓','거리 측정','↓','표면의 점'])
                for i in range(3):say(i)
            elif ci==2:
                c=cloud(D['scans'][0],BLUE);r=robot([0,0,0]);self.add(c,r)
                side(['Robot Frame','(0, 0, 0)','↓','첫 Map Frame'])
                say(0);axes=VGroup(Arrow(pos([0,0]),pos([1.3,0]),color=RED,buff=0),Arrow(pos([0,0]),pos([0,1.3]),color=GREEN,buff=0))
                say(1,Create(axes));say(2)
            elif ci==3:
                side(['Pose = (x, y, θ)','Encoder','↓','Odometry','↓','예상 Pose'])
                for i in range(3):say(i)
            elif ci==4:
                old=cloud(D['scans'][0],BLUE);cur=cloud(trans(D['scans'][1],D['predictions'][1]),ORANGE);self.add(old,cur)
                side(['파랑: 이전 Scan','주황: 현재 Scan','p′ = R p + t','R: 회전','t: 이동'])
                say(0)
                hs=D['histories'][1];anims=[Transform(cur,cloud(trans(D['scans'][1],p),ORANGE)) for p in hs[1::4]]
                say(1,Succession(*anims),run=5)
                say(2);say(3)
            elif ci==5:
                # Enlarged local comparison to make centimeter-scale correction visible.
                true=np.array(D['truth'][1]);pred=np.array(D['predictions'][1]);est=np.array(D['estimates'][1])
                def zoom(p):return np.array([-2+(p[0]-true[0])*28,(p[1]-true[1])*28,0])
                self.add(Dot(zoom(true),radius=.11,color=BLUE),txt('기준 위치',22,BLUE).move_to(zoom(true)+UP*.5))
                a=Dot(zoom(pred),radius=.13,color=ORANGE);b=Dot(zoom(est),radius=.13,color=GREEN);self.add(a)
                self.add(txt('위치 차이 확대 · sample 1',22,MUTED).move_to([-2,-2.1,0]))
                m=D['metrics'];side(['예상 위치 오차',f"{m['sample1_predicted_error_m']*100:.2f} cm",'보정 위치 오차',f"{m['sample1_corrected_error_m']*100:.2f} cm"])
                say(0);say(1,Transform(a,b),run=4);say(2)
            elif ci==6:
                im=grid_image(D['grids'][0]);self.add(im);side(['Occupancy Map','흰색: 빈 공간','파랑: 점유','회색: 미지','Scan → Map'])
                say(0)
                rec=next(r for r in A if r['chapter']==ci and r['line']==1)
                if subtitle:self.remove(subtitle)
                subtitle=txt(rec['caption'],26).move_to([0,-3.43,0]);self.add(subtitle)
                for g in D['grids'][1:]:
                    self.remove(im);im=grid_image(g);self.add(im);self.wait(rec['duration']/15)
                say(2)
            else:
                labels=['Motion','Scan','Match','Pose','Map Update'];nodes=VGroup()
                for i,s in enumerate(labels):
                    node=VGroup(RoundedRectangle(width=2.15,height=1.0,corner_radius=.12,color=BLUE),txt(s,25)).move_to([-5.1+i*2.55,.4,0]);nodes.add(node)
                self.add(nodes)
                for i in range(4):self.add(Arrow(nodes[i].get_right(),nodes[i+1].get_left(),buff=.07,color=MUTED))
                arrow=CurvedArrow(nodes[-1].get_bottom()+DOWN*.15,nodes[0].get_bottom()+DOWN*.15,angle=-TAU/5,color=GREEN);self.add(arrow)
                say(0,Succession(*[Indicate(n,color=ORANGE) for n in nodes]),run=6)
                self.add(txt('센서 관측 + 이동 정보 → 위치 추정 + 지도 갱신',29).move_to([0,1.85,0]));say(1);say(2)

class MapChapter(SlamLesson):
    only_chapter=6
