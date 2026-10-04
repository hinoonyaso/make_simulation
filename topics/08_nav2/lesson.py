"""Narration-paced Manim architecture and trace views; Blender fills spatial panels."""
from pathlib import Path
import json,numpy as np
from manim import *
from PIL import Image
R=Path(__file__).resolve().parent;D=json.loads((R/'output/trace.json').read_text());A=json.loads((R/'assets/audio/manifest.json').read_text());ST=json.loads((R/'storyboard.json').read_text())
BG='#F7F9FC';INK='#26364A';BLUE='#147DAD';GREEN='#198868';ORANGE='#D58525';RED='#B75057';MUTED='#738195';WALL='#586B80'
def txt(s,size=25,color=INK,width=None):
 t=Text(s,font='NanumGothic',font_size=size,color=color)
 if width and t.width>width:t.scale_to_fit_width(width)
 return t
def pos(p):return np.array([p[0]*.72-2.45,p[1]*.72,0])
def line(points,color=GREEN,width=5):return VMobject(color=color,stroke_width=width).set_points_as_corners([pos(p) for p in points])
def robot(p):
 return VGroup(Circle(.18,color=BLUE,fill_color=WHITE,fill_opacity=1).move_to(pos(p)),Arrow(pos(p),pos(p)+.38*np.array([np.cos(p[2]),np.sin(p[2]),0]),buff=0,color=BLUE,stroke_width=4,max_tip_length_to_length_ratio=.3))
def box(label,x,y,w=2.25,h=.7,color=BLUE,size=22):
 b=RoundedRectangle(width=w,height=h,corner_radius=.08,color=color,fill_color=WHITE,fill_opacity=1).move_to([x,y,0]);return VGroup(b,txt(label,size,width=w-.2).move_to(b))
def arrow(a,b,color=MUTED):return Arrow(a,b,buff=.08,color=color,stroke_width=3,max_tip_length_to_length_ratio=.15)
class Nav2Lesson(Scene):
 def construct(self):
  self.camera.background_color=BG;self.events=[]
  for ci,ch in enumerate(ST['chapters']):
   self.clear();self.add(txt(f'{ci+1:02d} / 10   ROS 2 · Nav2',18,MUTED).to_corner(UL,buff=.35),txt(ch['title'],33,width=12.7).move_to([0,3.05,0]),Line([-6.6,2.57,0],[6.6,2.57,0],color='#DAE2EB'),txt('교육용 모형 · 실제 Nav2 실행 아님 · 이상적 Pose 입력',16,MUTED).move_to([0,-2.85,0]));subtitle=None
   def say(li,action=None,seconds=3):
    nonlocal subtitle
    rec=next(a for a in A if a['chapter']==ci and a['line']==li)
    if subtitle:self.remove(subtitle)
    subtitle=txt(rec['caption'],24,width=13.0).move_to([0,-3.42,0]);self.add(subtitle)
    if action:action(min(seconds,rec['end']-self.time-.1))
    if rec['end']>self.time:self.wait(rec['end']-self.time)
   def side(lines,y=0,size=25):
    g=VGroup(*[txt(s,size,width=3.9) for s in lines]).arrange(DOWN,buff=.32).move_to([4.4,y,0]);self.add(g);return g
   def play(anim):return lambda t:self.play(anim,run_time=t)
   def room(costs=False):
    if costs:
     c=np.array(D['static_costmap']);rgb=np.empty((*c.shape,3),np.uint8);rgb[:]=[255,255,255];mask=(c>0)&(c<255);alpha=c[mask]/255;rgb[mask]=np.array([255,255,255])*(1-alpha[:,None])+np.array([240,171,77])*alpha[:,None];rgb[c>=255]=[127,137,151]
     im=Image.fromarray(rgb[::-1]).resize((732,492),Image.Resampling.NEAREST);p=R/'output/costmap.png';im.save(p);self.add(ImageMobject(str(p)).stretch_to_fit_width(9*.72).stretch_to_fit_height(6*.72).move_to(pos([0,0])))
    g=VGroup(Rectangle(width=9*.72,height=6*.72,color=WALL,stroke_width=3).move_to(pos([0,0])))
    for x0,y0,x1,y1 in D['boxes']:g.add(Rectangle(width=(x1-x0)*.72,height=(y1-y0)*.72,stroke_width=0,fill_color=WALL,fill_opacity=1).move_to(pos([(x0+x1)/2,(y0+y1)/2])))
    g.add(Circle(.2,color=GREEN).move_to(pos(D['goal'])),txt('G',15,GREEN).move_to(pos(D['goal'])+[0,.38,0]));self.add(g);return g
   def dynamic(row,path=True,sensor=False):
    g=VGroup(robot(row['pose']))
    if path:
     pp=D['dynamic']['plans'][row['path_id']]['path']
     if len(pp)>1:g.add(line(pp))
    if row['person'] is not None:g.add(Circle(D['person_radius']*.72,color=RED,fill_color=RED,fill_opacity=.6).move_to(pos(row['person'])))
    if row['detected'] is not None:g.add(Circle(.52*.72,color=ORANGE,stroke_width=2).move_to(pos(row['detected'])))
    if sensor:
     for j in range(0,120,2):
      if row['scan'][j]<3.15:g.add(Dot(pos(row['hits'][j]),radius=.025,color=BLUE))
    return g
   def playback(indices,seconds):
    frames=round(seconds*30);g=None
    for i,k in enumerate(indices):
     if g:self.remove(g)
     row=D['dynamic']['rows'][k];g=dynamic(row,sensor=True);self.add(g);self.events.append({'chapter':ci,'video_time':self.time,'sample':k,'simulation_time':row['time']});self.wait((round((i+1)*frames/len(indices))-round(i*frames/len(indices)))/30)
    return g
   if ci==0:
    room();r=robot(D['start']);self.add(r);p=side(['Goal Pose','x = 3.0 m','y = 0.0 m','yaw = 0 rad']);say(0)
    target=Arrow(pos(D['goal']),pos(D['goal'])+[.6,0,0],buff=0,color=GREEN);say(1,play(GrowArrow(target)));say(2)
   elif ci==1:
    inputs=[box(l,x,1.5,2.9) for l,x in [('Map',-4),('LiDAR',0),('Odometry',4)]];amcl=box('AMCL',0,0,3,color=GREEN);pose=box('Current Pose',0,-1.5,3,color=GREEN)
    self.add(*inputs,amcl,pose,*[arrow(b.get_bottom(),amcl.get_top()) for b in inputs],arrow(amcl.get_bottom(),pose.get_top()));say(0,play(Indicate(amcl,color=GREEN)),2);self.add(txt('실험에서는 이상적 Pose로 대체',22,ORANGE).move_to([4,-1.5,0]));say(1)
   elif ci==2:
    room(True);self.add(robot(D['start']));side(['Global Costmap','■ 막힌 영역','높은 비용: 장애물 근처','낮은 비용: 먼 곳','Inflation ≠ 모두 금지'],size=24);say(0);say(1,play(Indicate(Circle(.75,color=ORANGE).move_to(pos([-.6,2.05])))),3);say(2)
   elif ci==3:
    room(True);self.add(robot(D['start']));p=side(['Current Pose','+ Goal Pose','+ Global Costmap','↓ Planner','Global Path']);say(0)
    path=line(D['baseline']['plans'][0]['path']);say(1,play(Create(path)),5);self.remove(p);side(['A* 예시 구현','8방향 탐색','거리 + 비용','Path: 공간상의 경로','속도는 Controller가 계산'],size=24);say(2)
   elif ci==4:
    room();row=D['dynamic']['rows'][20];p=side(['LiDAR 관측점','지도에 없던 사람','↓','주변 장애물 갱신','Local Costmap']);g=dynamic(row,sensor=True);self.add(g)
    window=Rectangle(width=3.1,height=3.1,color=BLUE,stroke_width=3).move_to(pos(row['pose']));self.add(window);say(0);self.remove(g);say(1,lambda t:playback(range(20,35),t),6);say(2)
   elif ci==5:
    room(True);row=D['dynamic']['rows'][45];self.add(dynamic(row));panel=side(['Path + Local Costs','+ Pose / Velocity','+ 운동 제약','↓','Controller']);say(0)
    from model import propagate
    candidates=VGroup(*[line([propagate(np.array(row['pose']),v,w,t)[:2] for t in np.linspace(0,1.5,20)],'#B9C4D1',2) for v,w,_ in row['candidates']]);say(1,play(Create(candidates)),5)
    chosen=line([propagate(np.array(row['pose']),*row['cmd'],t)[:2] for t in np.linspace(0,1.5,20)],GREEN,7);say(2,play(Create(chosen)),4)
    self.remove(panel);v,w=row['cmd'];side(['cmd_vel',f'linear.x = {v:.2f} m/s',f'angular.z = {w:.2f} rad/s',f't = {row["time"]:.1f} s','선택한 명령의 예측'],size=24);say(3)
   elif ci==6:
    self.add(RoundedRectangle(width=8.3,height=4.4,corner_radius=.08,color='#DAE2EB').move_to([-2.2,-.25,0]));side(['cmd_vel','↓ Base Controller','ωL / ωR','↓ Wheels','AMR → 새 관측'],size=24);say(0)
    self.add(txt('r = 0.10 m   ·   L = 0.45 m',21).move_to([-2.2,2.15,0]));say(1);say(2)
   elif ci==7:
    self.add(RoundedRectangle(width=8.3,height=4.4,corner_radius=.08,color='#DAE2EB').move_to([-2.2,-.25,0]));p=side(['새 장애물 감지','↓','기존 경로 무효','↓ 정지 / Replan','새 Path 추종'],size=24);say(0);say(1);say(2)
    self.remove(p);m=D['dynamic']['metrics'];side(['둘 다 Goal 도달','장애물 없음: 14.0 s',f'장애물 있음: {m["duration_s"]:.1f} s',f'최소 외곽 간격: {m["minimum_clearance_m"]:.2f} m','모형 안에서의 결과'],size=23);say(3)
   elif ci==8:
    n=box('NavigateToPose',0,1.75,3.5);bt=box('Behavior Tree',0,.5,3.5,color=GREEN);planbox=box('ComputePathToPose',-3,-1,4);follow=box('FollowPath',3,-1,3);self.add(n,bt,planbox,follow,arrow(n.get_bottom(),bt.get_top()),arrow(bt.get_bottom(),planbox.get_top()),arrow(bt.get_bottom(),follow.get_top()));say(0)
    self.add(txt('RUNNING / SUCCESS / FAILURE',24,ORANGE).move_to([0,-2,0]));say(1,play(Indicate(bt,color=GREEN)),3);self.add(txt('트리 설정에 따른 재계획 · 복구 · 재시도',21).move_to([0,-2.48,0]));say(2)
   else:
    loc=box('Localization',-4.9,1.5,2.5);glob=box('Global Costmap',-1.7,1.5,2.8);goal=box('Goal',1.5,1.5,1.8);planner=box('Planner',1.5,0,1.8);path=box('Path',4.8,0,1.5,color=GREEN);local=box('Local Costmap',-1.7,-1.5,2.8);controller=box('Controller',1.5,-1.5,2.2);rob=box('Robot',4.8,-1.5,1.8,color=GREEN);sensor=box('Sensors',-4.9,-1.5,2.5)
    self.add(loc,glob,goal,planner,path,local,controller,rob,sensor,arrow(goal.get_bottom(),planner.get_top()),arrow(glob.get_right(),planner.get_left()),arrow(loc.get_bottom(),planner.get_left()),arrow(planner.get_right(),path.get_left()));say(0)
    self.add(arrow(sensor.get_top(),loc.get_bottom()),arrow(sensor.get_right(),local.get_left()),arrow(sensor.get_top(),glob.get_bottom()));say(1)
    self.add(arrow(path.get_bottom(),controller.get_top()),arrow(local.get_right(),controller.get_left()),arrow(controller.get_right(),rob.get_left()),txt('cmd_vel',16).move_to([3.3,-1.08,0]));feedback=VMobject(color=GREEN,stroke_width=3).set_points_as_corners([rob.get_bottom(),[4.8,-2.35,0],[-4.9,-2.35,0],sensor.get_bottom()]);self.add(feedback,txt('이동 → 관측 피드백',17,GREEN).move_to([0,-2.55,0]));say(2,play(Create(feedback)),3);self.add(txt('Behavior Tree: 전체 실행 조율',20,ORANGE).move_to([4.4,1.65,0]));say(3)
  (R/'output/render_events.json').write_text(json.dumps(self.events,ensure_ascii=False,indent=2))
