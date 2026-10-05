"""Continuous Manim dissection of the DWB-only candidate trace."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parents[1]
sys.path.insert(0, str(BUNDLE / "core/manim-robotics-education-skill/templates"))
from manim_kit import P, BeatClock, beat_seconds, turtlebot3_top, world_window  # noqa: E402

TOP_WIDTH = 5.6
XFADE = 0.6
W = world_window(TOP_WIDTH)
K = W.k
TRACE = json.loads((HERE / "data/candidate_trace.json").read_text(encoding="utf-8"))
SAMPLES = TRACE["samples"]
POSE = TRACE["pose"]
OX, OY = TRACE["obstacle"]
OR, RR = TRACE["obstacle_radius"], TRACE["robot_radius"]
SELECTED = SAMPLES[TRACE["selected_index"]]
VALID = [s for s in SAMPLES if s["valid"]]
RANKED = sorted(VALID, key=lambda s: s["score"])
TOP = RANKED[:8]
INVALID = [s for s in SAMPLES if not s["valid"]]
INVALID_WORST = min(INVALID, key=lambda s: s["minimum_clearance"])
B2, B3, B4, B5, B6 = beat_seconds(HERE / "visual_manifest.json", "B02", "B03", "B04", "B05", "B06")

DRUM = "#D9542C"
PREDICT = P.learned
SELECT = P.active
EXECUTED = P.sensor


def make_world():
    walls = VGroup(*[
        Line(W(-3.9, side * (TRACE["corridor_half_width"] + .03)),
             W(3.9, side * (TRACE["corridor_half_width"] + .03)), color=P.muted, stroke_width=5)
        for side in (-1, 1)
    ])
    centerline = DashedLine(W(-3.0, 0), W(3.0, 0), dash_length=.11 * K,
                            dashed_ratio=.52, color=P.faint, stroke_width=3)
    goal = Circle(radius=.16 * K, color=P.result, stroke_width=4).move_to(W(3.0, 0))
    drum = Circle(radius=OR * K, fill_color=DRUM, fill_opacity=1,
                  stroke_color="#F08A62", stroke_width=3).move_to(W(OX, OY))
    bot = turtlebot3_top(W, POSE)
    return VGroup(walls, centerline, goal, drum), bot, drum


def trajectory(candidate, color, width=3.5, opacity=.58):
    points = [W(p[0], p[1]) for p in candidate["trajectory"]]
    return VMobject(color=color, stroke_width=width, stroke_opacity=opacity).set_points_as_corners(points)


def point_on(candidate, t):
    pts = np.asarray(candidate["trajectory"], dtype=float)
    idx = float(np.clip(t, 0, len(pts) - 1))
    i = min(int(idx), len(pts) - 2)
    f = idx - i
    return (1 - f) * pts[i] + f * pts[i + 1]


def cost_panel():
    rows = [
        ("경로", SELECTED["costs"][0], P.sensor),
        ("목표", SELECTED["costs"][1], P.fg),
        ("장애물", SELECTED["costs"][2], P.error),
        ("속도", SELECTED["costs"][3], P.result),
        ("회전", SELECTED["costs"][4], P.learned),
    ]
    items = VGroup()
    for name, value, color in rows:
        label = Text(name, font="NanumGothic", font_size=24, color=color)
        number = DecimalNumber(value, num_decimal_places=3, font_size=24, color=P.fg)
        items.add(VGroup(label, number).arrange(RIGHT, buff=.20, aligned_edge=DOWN))
    items.arrange(DOWN, aligned_edge=LEFT, buff=.18)
    heading = Text("선택 후보의 가중 비용", font="NanumGothic", font_size=29, color=P.fg, weight=BOLD)
    heading.next_to(items, UP, buff=.27, aligned_edge=LEFT)
    total = Text(f"합계  {SELECTED['score']:.3f}", font="NanumGothic", font_size=29,
                 color=SELECT, weight=BOLD).next_to(items, DOWN, buff=.30, aligned_edge=LEFT)
    panel = VGroup(heading, items, total).move_to([4.45, .00, 0])
    return panel


class DWBDissection(MovingCameraScene):
    def construct(self):
        self.camera.background_color = P.bg
        world, bot, drum = make_world()
        self.add(world, bot)
        self.wait(XFADE)  # matches the Blender crane's top-view end frame

        # B02: candidates emerge from a shared real source pose.
        paths = [trajectory(c, P.learned if c is not SELECTED else SELECT, opacity=.30)
                 for c in TOP]
        count_label = Text(f"실제 후보 {TRACE['candidate_count']}개 · 상위 8개 경로 표시",
                           font="NanumGothic", font_size=27, color=P.fg).to_edge(UP, buff=.35)
        cmd_rows = VGroup(*[
            Text(f"v {c['cmd'][0]:.3f}   ω {c['cmd'][1]:.3f}", font="DejaVu Sans", font_size=20,
                 color=SELECT if c is SELECTED else P.muted)
            for c in TOP
        ]).arrange(DOWN, aligned_edge=LEFT, buff=.10).move_to([4.5, -.1, 0])
        with BeatClock(self, B2) as beat:
            self.add(count_label)
            beat.play(LaggedStart(*[Create(p) for p in paths], lag_ratio=.09), run_time=2.2)
            beat.play(FadeIn(cmd_rows, shift=LEFT * .16), run_time=.8)

        # B03: one predicted path is followed to the model's 2 s horizon.
        chosen_path = paths[TOP.index(SELECTED)]
        marker = Dot(W(*point_on(SELECTED, 0)[:2]), radius=.085, color=SELECT)
        horizon = Text("예측 범위  2.0 s", font="DejaVu Sans", font_size=28, color=P.fg)
        horizon.to_edge(UP, buff=.35)
        with BeatClock(self, B3) as beat:
            beat.play(Transform(count_label, horizon), run_time=.45)
            beat.play(FadeIn(marker), run_time=.35)
            beat.play(UpdateFromAlphaFunc(marker, lambda m, a: m.move_to(W(*point_on(SELECTED, 20*a)[:2])),
                                          run_time=3.0), run_time=3.0)
            clearance_label = Text(f"최소 여유 {SELECTED['minimum_clearance']:.3f} m",
                                   font="DejaVu Sans", font_size=25, color=P.error)
            clearance_label.next_to(drum, DOWN, buff=.28).shift(RIGHT * .58)
            beat.play(FadeIn(clearance_label), chosen_path.animate.set_stroke(width=6, opacity=1), run_time=.6)

        # B04: costs are read directly from the selected source candidate.
        panel = cost_panel()
        sum_label = Text("총비용 = 가중 항목의 합", font="NanumGothic",
                         font_size=24, color=P.fg).move_to([4.35, 2.40, 0])
        with BeatClock(self, B4) as beat:
            beat.play(FadeOut(cmd_rows), FadeIn(panel, shift=LEFT * .22), FadeIn(sum_label), run_time=1.2)
            beat.play(chosen_path.animate.set_stroke(width=7, opacity=1), run_time=.7)

        # B05: threshold filtering and minimum valid score.
        invalid_path = trajectory(INVALID_WORST, P.error, width=4, opacity=.9)
        filter_text = Text(f"여유 0.09 m 미만 제외   ·   {TRACE['valid_count']} / {TRACE['candidate_count']} 유효",
                           font="NanumGothic", font_size=25, color=P.fg).to_edge(UP, buff=.35)
        selected_text = Text(f"선택  v {SELECTED['cmd'][0]:.3f}  |  ω {SELECTED['cmd'][1]:.3f}",
                             font="DejaVu Sans", font_size=22, color=SELECT, weight=BOLD)
        selected_text.move_to([4.30, -2.70, 0])
        with BeatClock(self, B5) as beat:
            beat.play(FadeIn(invalid_path), Transform(count_label, filter_text), run_time=.7)
            beat.play(AnimationGroup(*[p.animate.set_stroke(opacity=.10) for p in paths
                                       if p is not chosen_path]),
                      invalid_path.animate.set_stroke(opacity=.95), run_time=.8)
            beat.play(FadeIn(selected_text), run_time=.6)

        # B06: retain the selected prediction, execute only its first 0.2 s.
        start = np.asarray(POSE, dtype=float)
        next_pose = np.asarray(SELECTED["trajectory"][2], dtype=float)
        first_segment = Line(W(*start[:2]), W(*next_pose[:2]), color=EXECUTED, stroke_width=10)
        next_bot = turtlebot3_top(W, next_pose)
        dt_label = Text("실행 구간  0.2 s", font="NanumGothic", font_size=27,
                        color=EXECUTED, weight=BOLD).move_to([4.25, -2.55, 0])
        with BeatClock(self, B6) as beat:
            beat.play(AnimationGroup(*[p.animate.set_stroke(opacity=.10) for p in paths
                                       if p is not chosen_path]),
                      chosen_path.animate.set_stroke(opacity=.36, width=4),
                      FadeOut(VGroup(panel, sum_label, selected_text)), run_time=.7)
            beat.play(Create(first_segment), FadeIn(dt_label), run_time=.5)
            beat.play(Transform(bot, next_bot), run_time=1.8, rate_func=smooth)
            executed_point = Dot(W(*next_pose[:2]), radius=.085, color=EXECUTED)
            beat.play(FadeIn(executed_point), run_time=.25)


if __name__ == "__main__":
    config.pixel_width, config.pixel_height, config.frame_rate = 1920, 1080, 30
