from pathlib import Path
import json,numpy as np
from manim import *
R=Path(__file__).resolve().parent;D=json.loads((R/'output/trace.json').read_text());A=json.loads((R/'assets/audio/manifest.json').read_text());ST=json.loads((R/'storyboard.json').read_text())
BG='#F7F9FC';INK='#26364A';BLUE='#83CDDF';PURPLE='#C1AADB';ORANGE='#F0AB4D';GREEN='#198868';WALL='#586B80';MUTED='#738195'
def txt(s,size=26,color=INK):return Text(s,font='NanumGothic',font_size=size,color=color)
def pos(p):return np.array([(p[0]-5.5)*.54-2,(4-p[1])*.54,0])
class Grid:
 def __init__(self,scene):
  self.scene=scene;self.cells={};self.stats=None
  for y in range(D['height']):
   for x in range(D['width']):
    q=Square(.515,stroke_color='#D1DBE6',stroke_width=1,fill_color=WALL if [x,y] in D['blocked'] else WHITE,fill_opacity=1).move_to(pos([x,y]));self.cells[x,y]=q
  self.group=VGroup(*self.cells.values());scene.add(self.group)
  self.labels=VGroup(txt('S',21,WHITE).move_to(pos(D['start'])),txt('G',21,WHITE).move_to(pos(D['goal'])));self.reset();scene.add(self.labels)
 def reset(self):
  for n,q in self.cells.items():q.set_fill(WALL if list(n) in D['blocked'] else WHITE)
  self.cells[tuple(D['start'])].set_fill(GREEN);self.cells[tuple(D['goal'])].set_fill('#B75057')
 def state(self,row,stats=False):
  self.reset()
  for n in row['closed']:self.cells[tuple(n)].set_fill(PURPLE)
  for n in row['open']:self.cells[tuple(n)].set_fill(BLUE)
  self.cells[tuple(row['current'])].set_fill(ORANGE)
  for n,c in [(D['start'],GREEN),(D['goal'],'#B75057')]:self.cells[tuple(n)].set_fill(c)
  self.scene.add(self.labels)
  if stats:
   if self.stats:self.scene.remove(self.stats)
   self.stats=VGroup(txt(f"g = {row['g']}   h = {row['h']}",25),txt(f"f = {row['f']}",30),txt(f"Open {len(row['open'])} / Closed {len(row['closed'])}",22)).arrange(DOWN,buff=.2).move_to([4.25,-1.55,0]);self.scene.add(self.stats)
 def run(self,rows,seconds,stats=False):
  n=len(rows);frames=round(seconds*30)
  for i,row in enumerate(rows):
   self.state(row,stats)
   self.scene.events.append(dict(video_time=self.scene.time,chapter=self.scene.chapter,search_step=row['step'],current=row['current'],f=row['f']))
   self.scene.wait((round((i+1)*frames/n)-round(i*frames/n))/30)
 def line(self,path,color=GREEN,width=8):return VMobject(color=color,stroke_width=width).set_points_as_corners([pos(p) for p in path])

def parent_path(row,node):
 p={tuple(r['node']):r['parent'] for r in row['parents']};path=[node]
 while path[-1]!=D['start']:path.append(p[tuple(path[-1])])
 return path[::-1]

class AStarLesson(Scene):
 def construct(self):
  self.camera.background_color=BG;self.events=[];rows=D['astar']['rows'];sample=rows[D['metrics']['cell_example']['step']]
  for ci,ch in enumerate(ST['chapters']):
   self.chapter=ci;self.clear();self.add(txt(f'{ci+1:02d} / 08   A*',19,MUTED).to_corner(UL,buff=.35));self.add(txt(ch['title'],34).move_to([0,3.05,0]));self.add(Line([-6.6,2.57,0],[6.6,2.57,0],color='#DAE2EB'));self.add(txt('실제 탐색 기록 · 4방향 · 한 칸 비용 1',16,MUTED).move_to([0,-2.83,0]));subtitle=None
   def say(li,action=None,seconds=3):
    nonlocal subtitle
    rec=next(a for a in A if a['chapter']==ci and a['line']==li)
    if subtitle:self.remove(subtitle)
    subtitle=txt(rec['caption'],25).move_to([0,-3.42,0]);self.add(subtitle)
    if action:action(seconds)
    if rec['end']>self.time:self.wait(rec['end']-self.time)
   def side(lines,y=0,size=25):
    g=VGroup(*[txt(s,size) for s in lines]).arrange(DOWN,buff=.35).move_to([4.25,y,0]);self.add(g);return g
   def play(anim):return lambda t:self.play(anim,run_time=t)
   if ci==0:
    grid=Grid(self);side(['S: Start','G: Goal','회색: 장애물','↔ ↕  4방향','한 칸 비용 = 1'])
    say(0);say(1);say(2,play(Indicate(grid.cells[tuple(D['goal'])],color=ORANGE)))
   elif ci==1:
    grid=Grid(self);panel=side(['Dijkstra','작은 g부터 선택','목적지 예상 비용 없음'])
    say(0,lambda t:grid.run(D['dijkstra']['rows'][:45],t),8)
    say(1,lambda t:grid.run(D['dijkstra']['rows'][45:],t),6)
    self.remove(panel);side(['목적지까지','남은 예상 비용도','활용한다면?'])
    say(2)
   elif ci==2:
    grid=Grid(self);n=sample['current'];self.add(SurroundingRectangle(grid.cells[tuple(n)],color=ORANGE,buff=.035))
    panel=side(['f(n) = g(n) + h(n)','g: 지나온 비용','h: 남은 예상 비용','f: 예상 총비용'],size=26)
    gline=grid.line(parent_path(sample,n),GREEN,7);say(0,play(Create(gline)),4)
    mid=[D['goal'][0],n[1]];hline=VGroup(DashedLine(pos(n),pos(mid),color='#D58525',stroke_width=6),DashedLine(pos(mid),pos(D['goal']),color='#D58525',stroke_width=6))
    say(1,play(Create(hline)),4);say(2,play(Indicate(panel[0],color=ORANGE)),2)
   elif ci==3:
    grid=Grid(self);grid.state(rows[sample['step']-1]);self.add(SurroundingRectangle(grid.cells[tuple(sample['current'])],color='#D58525',buff=.04,stroke_width=5))
    side(['n = (5, 5)','g = 5','h = 5 + 2 = 7','f = 5 + 7 = 12','Open 최소 f = 12'],size=25)
    gline=grid.line(parent_path(sample,sample['current']),GREEN,6);say(0,play(Create(gline)),3)
    mid=[D['goal'][0],sample['current'][1]];hline=VGroup(DashedLine(pos(sample['current']),pos(mid),color='#D58525',stroke_width=5),DashedLine(pos(mid),pos(D['goal']),color='#D58525',stroke_width=5));say(1,play(Create(hline)),3)
    self.remove(gline,hline)
    nums=VGroup(*[txt(str(c['f']),16).move_to(pos(c['node'])) for c in sample['candidates']]);self.add(nums)
    say(2,play(Indicate(grid.cells[tuple(sample['current'])],color=ORANGE)),2)
   elif ci==4:
    grid=Grid(self);side(['Open: 대기 후보','Current: 현재 칸','Closed: 처리한 칸'],y=1,size=24)
    # Legend swatches make labels independent of color perception.
    for y,c in [(1.6,BLUE),(1.05,ORANGE),(.5,PURPLE)]:self.add(Square(.18,stroke_width=0,fill_color=c,fill_opacity=1).move_to([2.4,y,0]))
    say(0,lambda t:grid.run(rows[:8],t,True),7)
    say(1,lambda t:grid.run(rows[8:16],t,True),7)
    say(2,lambda t:grid.run(rows[16:24],t,True),7)
   elif ci==5:
    grid=Grid(self);grid.state(rows[23]);panel=side(['장애물 제외','h는 벽을 무시한','낮은 예상 비용','로봇은 아직 정지'])
    wall=VGroup(*[grid.cells[(6,y)] for y in range(1,8)]);say(0,play(Indicate(wall,color='#D05D4F')),3)
    say(1,lambda t:grid.run(rows[24:40],t),9)
    self.remove(panel);side(['Manhattan h','과대평가하지 않음','일관성 만족','↓','최단 경로 보장'],size=24)
    say(2);say(3)
   elif ci==6:
    grid=Grid(self);grid.state(rows[-1]);panel=side(['Goal 선택','↓','parent 역추적','↓','Start'])
    reverse=D['astar']['path'][::-1];segments=VGroup(*[Line(pos(a),pos(b),color=GREEN,stroke_width=8) for a,b in zip(reverse,reverse[1:])]);say(0,play(LaggedStart(*[Create(s) for s in segments],lag_ratio=.15)),7)
    grid.reset();self.add(segments);self.remove(panel);panel=side(['Final Path','16회 이동','총비용 = 16']);say(1)
    self.remove(panel);side(['같은 경로 비용 16','꺼낸 칸 (Goal 포함)','A*: 41','Dijkstra: 89','지도·동점 규칙에 따라 다름'],size=23);say(2)
   else:
    self.add(txt('SLAM: 지도 → AMCL: 위치 → A*: 경로',28).move_to([0,1.9,0]))
    labels=[['Occupancy','Grid'],['Global','Costmap'],['Global','Planner'],['Global','Path'],['Controller','속도 명령']];nodes=[]
    for x,lines in zip([-5.2,-2.6,0,2.6,5.2],labels):
     box=RoundedRectangle(width=2.25,height=1.25,corner_radius=.1,color='#147DAD',fill_color=WHITE,fill_opacity=1).move_to([x,.1,0]);label=VGroup(*[txt(s,23) for s in lines]).arrange(DOWN,buff=.15).move_to(box);g=VGroup(box,label);self.add(g);nodes.append(g)
    for i in range(4):self.add(Arrow(nodes[i].get_right(),nodes[i+1].get_left(),buff=.06,color=MUTED))
    self.add(txt('장애물·로봇 크기 반영',24).move_to([-2.6,-1.1,0]));say(0)
    self.add(txt('NavFn의 use_astar 등, 플래너 설정에 따라 선택',23).move_to([0,-1.65,0]));say(1)
    self.add(txt('다음 편: Nav2',30,GREEN).move_to([0,-2.3,0]));say(2,play(Indicate(nodes[-1],color=GREEN)),2)
  (R/'output/render_events.json').write_text(json.dumps(self.events,ensure_ascii=False,indent=2))
