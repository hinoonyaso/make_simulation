"""A* global route into a separate DWB educational trace, shown as continuous state changes."""
import json
import sys
from pathlib import Path
import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import P, BeatClock, beat_seconds, turtlebot3_top, world_window  # noqa: E402

ASTAR = json.loads((HERE / "data/astar_trace.json").read_text(encoding="utf-8"))
DWB = json.loads((HERE / "data/dwb_trace.json").read_text(encoding="utf-8"))
AT = ASTAR["samples"][0]
DW = DWB["samples"]
SELECTED = DW[DWB["selected_index"]]
RANKED = sorted((s for s in DW if s["valid"]), key=lambda s: s["score"])
DISPLAY = RANKED[:9]
W = world_window(5.5)
K = W.k
DRUM = "#D9542C"
SELECT = P.active

def label(text, size=30, color=None, bold=False):
    return Text(text, font="NanumGothic", font_size=size, color=color or P.fg,
                weight=BOLD if bold else NORMAL)

def grid_group():
    cell = .49
    ox = -2.95
    oy = -2.05
    def cpos(x, y): return np.array([ox + (x + .5) * cell, oy + (y + .5) * cell, 0])
    blocked = set(map(tuple, ASTAR["blocked"]))
    cells = VGroup()
    lines = VGroup()
    for y in range(ASTAR["height"]):
        for x in range(ASTAR["width"]):
            rect = Square(side_length=cell, stroke_color="#59616C", stroke_width=1.3)
            rect.move_to(cpos(x, y))
            if (x, y) in blocked:
                rect.set_fill(DRUM, opacity=.88).set_stroke("#F08A62", 1)
            else:
                rect.set_fill(P.bg, opacity=.05)
            cells.add(rect)
    for x, y in AT["path"]:
        lines.add(Dot(cpos(x, y), radius=.055, color=P.learned))
    line = VMobject(color=P.learned, stroke_width=8).set_points_as_corners([cpos(x,y) for x,y in AT["path"]])
    start = Dot(cpos(*ASTAR["start"]), radius=.13, color=P.sensor)
    goal = Circle(radius=.15, color=P.result, stroke_width=4).move_to(cpos(*ASTAR["goal"]))
    return VGroup(cells, line, start, goal), line, cpos

def dwb_world():
    walls = VGroup(*[
        Line(W(-3.9, side * (DWB["corridor_half_width"] + .03)),
             W(3.9, side * (DWB["corridor_half_width"] + .03)), color=P.muted, stroke_width=5)
        for side in (-1, 1)
    ])
    path = DashedLine(W(-3,0), W(3,0), dash_length=.11*K, dashed_ratio=.5,
                      color=P.faint, stroke_width=3)
    ox, oy = DWB["obstacle"]
    drum = Circle(radius=DWB["obstacle_radius"]*K, fill_color=DRUM, fill_opacity=1,
                  stroke_color="#F08A62", stroke_width=3).move_to(W(ox, oy))
    bot = turtlebot3_top(W, DWB["pose"])
    goal = Circle(radius=.15*K, color=P.result, stroke_width=4).move_to(W(3,0))
    return VGroup(walls, path, drum, goal), bot, drum

def rollout(sample, color, opacity=.5, width=3):
    pts = [W(p[0],p[1]) for p in sample["trajectory"]]
    return VMobject(color=color, stroke_width=width, stroke_opacity=opacity).set_points_as_corners(pts)

class AStarDWB(MovingCameraScene):
    def construct(self):
        self.camera.background_color = P.bg
        b1,b2,b3,b4,b5,b6,b7 = beat_seconds(HERE/"visual_manifest.json", "B01","B02","B03","B04","B05","B06","B07")
        title = label("한 로봇, 두 시간 범위", 40, bold=True).to_edge(UP, buff=.4)
        # Beat 1: physical intuition, then the question target.
        world, bot, drum = dwb_world()
        with BeatClock(self,b1) as beat:
            self.add(world, bot, title)
            question = label("길 전체와 바로 앞 움직임, 누가 맡을까?", 31, P.fg)
            question.to_edge(DOWN, buff=.46)
            beat.play(FadeIn(question, shift=UP*.12), run_time=1.2)
            beat.wait(2.2)
        # Beat 2: reveal the recorded A* path in its own grid model.
        grid, route, cpos = grid_group()
        title2 = label("A*  전역 경로", 38, bold=True).to_edge(UP, buff=.4)
        cost = label(f"경로 비용  {AT['cost']}칸", 27, P.result).to_corner(UR, buff=.55)
        with BeatClock(self,b2) as beat:
            beat.play(FadeOut(VGroup(world,bot,question,title)), run_time=.5)
            self.remove(world,bot,question,title)
            beat.play(FadeIn(title2), run_time=.45)
            self.add(grid[0], grid[2], grid[3])
            beat.play(Create(route), run_time=2.2)
            beat.play(FadeIn(cost), run_time=.6)
        # Beat 3: keep A* visible while distinctly introducing the independent DWB case.
        boundary = label("별도 기록 사례", 23, P.error, bold=True).to_corner(UR,buff=.5)
        role = label("A*는 목적지까지의 길을 제안", 28, P.fg).to_edge(DOWN,buff=.4)
        with BeatClock(self,b3) as beat:
            beat.play(FadeOut(cost), run_time=.35)
            beat.play(FadeIn(boundary), FadeIn(role), run_time=.45)
            beat.play(grid.animate.scale(.76).shift(LEFT*3.05+UP*.08), run_time=1.0)
            # A separate local scene appears beside the grid; no shared coordinates are implied.
            local = label("DWB형 모형", 30, P.sensor, bold=True).move_to([3.05,2.15,0])
            local_line = Line([1.05,.1,0],[5.85,.1,0],color=P.muted,stroke_width=4)
            local_bot = turtlebot3_top(world_window(1.3), [-.2,0,0]).scale(.84).move_to([1.6,.1,0])
            local_drum = Circle(radius=.44,fill_color=DRUM,fill_opacity=1,stroke_color="#F08A62",stroke_width=3).move_to([3.7,.1,0])
            local_goal = Circle(radius=.18,color=P.result,stroke_width=3).move_to([5.4,.1,0])
            local_group = VGroup(local_line,local_bot,local_drum,local_goal,local)
            beat.play(FadeIn(local_group,shift=LEFT*.15), run_time=1.0)
            handoff = label("A* 격자 trace     /     DWB 후보 trace", 22, P.muted).to_edge(DOWN,buff=.35)
            beat.play(FadeOut(role), run_time=.25)
            self.remove(role)
            beat.play(FadeIn(handoff), run_time=.35)
        # Beat 4: transition into the source DWB obstacle trace, retain the evidence boundary.
        dwb_group, dwb_bot, dwb_drum = dwb_world()
        count = label(f"속도 후보  {DWB['candidate_count']}개", 29, P.fg).to_edge(UP,buff=.35)
        with BeatClock(self,b4) as beat:
            beat.play(FadeOut(VGroup(grid[0],route,grid[2],grid[3],local_group,handoff,boundary,title2)), run_time=.55)
            self.remove(grid[0],route,grid[2],grid[3],local_group,handoff,boundary,title2)
            beat.play(FadeIn(dwb_group), FadeIn(dwb_bot), run_time=.55)
            beat.play(FadeIn(boundary), run_time=.35)
            self.add(count)
            paths = [rollout(s, P.learned if s is not SELECTED else SELECT, .30 if s is not SELECTED else .9,
                             3 if s is not SELECTED else 5) for s in DISPLAY]
            beat.play(LaggedStart(*[Create(p) for p in paths], lag_ratio=.07), run_time=2.3)
        # Beat 5: pick and explain the selected two-second prediction.
        chosen_path = paths[DISPLAY.index(SELECTED)]
        chosen_label = label(f"선택  v={SELECTED['cmd'][0]:.2f} m/s   ω={SELECTED['cmd'][1]:.3f} rad/s", 25, SELECT, True)
        chosen_label.to_edge(DOWN,buff=.37)
        score = label(f"유효 {DWB['valid_count']} / {DWB['candidate_count']}   ·   점수 {SELECTED['score']:.3f}   ·   예측 2초", 24, P.fg)
        score.next_to(count,DOWN,buff=.28)
        with BeatClock(self,b5) as beat:
            beat.play(AnimationGroup(*[p.animate.set_stroke(opacity=.10) for p in paths if p is not chosen_path]),
                      chosen_path.animate.set_stroke(opacity=1,width=7), run_time=.8)
            beat.play(FadeIn(score),FadeIn(chosen_label),run_time=.8)
            marker = Dot(W(*SELECTED["trajectory"][0][:2]),radius=.09,color=SELECT)
            beat.play(FadeIn(marker), UpdateFromAlphaFunc(marker,lambda m,a:m.move_to(W(*SELECTED["trajectory"][int(20*a)][:2])),run_time=4.0),run_time=4.0)
        # Beat 6: execute one control interval, then re-evaluate from the new pose.
        nextpose = SELECTED["trajectory"][2]
        segment = Line(W(*DWB["pose"][:2]),W(*nextpose[:2]),color=P.sensor,stroke_width=10)
        interval = label("이번에 적용  0.2초",27,P.sensor,True).to_corner(DL,buff=.55)
        refreshed = [rollout(s,P.learned,.25,2.6) for s in DISPLAY]
        nextbot = turtlebot3_top(W,nextpose)
        with BeatClock(self,b6) as beat:
            beat.play(FadeOut(boundary), run_time=.35)
            self.remove(boundary)
            beat.play(FadeOut(VGroup(score,chosen_label)), chosen_path.animate.set_stroke(opacity=.28,width=4),
                      Create(segment),FadeIn(interval),run_time=.8)
            self.remove(score,chosen_label)
            beat.play(Transform(dwb_bot,nextbot),run_time=1.3)
            beat.play(LaggedStart(*[Create(p) for p in refreshed],lag_ratio=.05),run_time=1.7)
            again=label("새 위치에서 다시 비교",25,P.result).to_corner(UR,buff=.5)
            beat.play(FadeIn(again),run_time=.5)
        # Beat 7: summarize the two roles and the model boundary.
        recap=label("A*  길 전체     →     DWB형  다음 속도",34,P.fg,True).move_to([0,1.45,0])
        disclaimer=label("서로 다른 trace 기반 교육용 모형 · Nav2 DWB 실행 아님",23,P.muted).move_to([0,-1.55,0])
        with BeatClock(self,b7) as beat:
            self.remove(dwb_group,dwb_bot,*paths,*refreshed,segment,interval,again,count,boundary)
            beat.play(FadeIn(recap,shift=UP*.15),FadeIn(disclaimer),run_time=.65)
            beat.wait(1.2)

if __name__ == "__main__":
    config.pixel_width, config.pixel_height, config.frame_rate = 1920,1080,30
