"""S2 (beats B02-B06): top-view dissection of one TEB-style band optimisation.

Values come only from data/band_trace.json; beat lengths come from visual_manifest.json (narration).
The first frame matches the Blender S1 end frame (world_window(TOP_WIDTH)), held for XFADE seconds.

uv run manim -ql --fps 15 pilots/01_teb_reference/manim_shot.py BandDissection   # preview
uv run manim -qh --fps 30 pilots/01_teb_reference/manim_shot.py BandDissection   # final 1080p30
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "core/manim-robotics-education-skill/templates"))
from manim_kit import P, BeatClock, beat_seconds, turtlebot3_top, world_window  # noqa: E402

TOP_WIDTH = 5.6  # must equal blender_shots.TOP_WIDTH
XFADE = 0.6      # must equal assemble.XFADE
W = world_window(TOP_WIDTH)
K = W.k
DATA = json.loads((HERE / "data/band_trace.json").read_text(encoding="utf-8"))
SNAP = DATA["samples"]
OX, OY = DATA["obstacle"]
OR, RR = DATA["obstacle_radius"], DATA["robot_radius"]
MARGIN = 0.20  # topics/09 model: obstacle residual is active when clearance < 0.20 m
HALF = DATA["corridor_half_width"]
CONVERGED = 12  # snapshots 12..24 are identical in the source trace
DRUM = "#D9542C"
BAND_C = P.learned
COSTS = [("cost_obstacle", P.error, "장애물"), ("cost_time", P.sensor, "시간"),
         ("cost_kinematics", P.active, None), ("cost_via", P.result, None), ("cost_smooth", P.muted, None)]
B02, B03, B04, B05, B06 = beat_seconds(HERE / "visual_manifest.json", "B02", "B03", "B04", "B05", "B06")


def clearance(x, y):
    return math.hypot(x - OX, y - OY) - OR - RR


def advance(p, v, w, dt):
    x, y, th = p
    if abs(w) < 1e-8:
        return [x + v * dt * math.cos(th), y + v * dt * math.sin(th), th]
    return [x + v / w * (math.sin(th + w * dt) - math.sin(th)),
            y + v / w * (-math.cos(th + w * dt) + math.cos(th)), th + w * dt]


def snapshot(s):
    """Snapshots are real optimiser states; values between them are a visual tween."""
    s = float(np.clip(s, 0, len(SNAP) - 1))
    i = min(int(s), len(SNAP) - 2)
    f = s - i
    a, b = SNAP[i], SNAP[i + 1]
    poses = (1 - f) * np.array(a["poses"]) + f * np.array(b["poses"])
    dts = (1 - f) * np.array(a["dt"]) + f * np.array(b["dt"])
    geo = lambda k: math.exp((1 - f) * math.log(a[k] + 1e-9) + f * math.log(b[k] + 1e-9))
    return poses, dts, {k: geo(k) for k, _, _ in COSTS}, geo("objective")


def danger_color(x, y):
    t = float(np.clip((clearance(x, y) - (MARGIN - 0.04)) / 0.08, 0, 1))
    return interpolate_color(ManimColor(P.error), ManimColor(BAND_C), t)


def band(poses, focus=0.0):
    """focus in [0,1]: 0 = whole band, 1 = only segment 0 (executed) stays bright."""
    pts = [W(p[0], p[1]) for p in poses]
    segs, dots = VGroup(), VGroup()
    rest = 1 - .78 * focus
    for i, (a, b, pa, pb) in enumerate(zip(pts, pts[1:], poses, poses[1:])):
        col = danger_color(*(np.array(pa[:2]) + np.array(pb[:2])) / 2)
        if i == 0:
            col = interpolate_color(col, ManimColor(P.active), focus)
        segs.add(Line(a, b, color=col, stroke_width=6 + 3 * focus * (i == 0), stroke_opacity=1 if i == 0 else rest))
    for i, (p, pp) in enumerate(zip(pts, poses)):
        dots.add(Dot(p, radius=.075, color=danger_color(pp[0], pp[1]), fill_opacity=1 if i <= 1 else rest))
    return VGroup(segs, dots)


class BandDissection(MovingCameraScene):
    def construct(self):
        self.camera.background_color = P.bg
        pose0 = DATA["pose"]
        # --- static layout identical to the Blender top view ---
        walls = VGroup(*[Line(W(-3.9, s * (HALF + .03)), W(3.9, s * (HALF + .03)), color=P.muted, stroke_width=5)
                         for s in (-1, 1)])
        path = DashedLine(W(-3.0, 0), W(3.0, 0), dash_length=.1 * K, dashed_ratio=.5, color=P.faint, stroke_width=3)
        goal = Circle(radius=.16 * K, color=P.result, stroke_width=4).move_to(W(3.0, 0))
        drum = Circle(radius=OR * K, fill_color=DRUM, fill_opacity=1, stroke_color="#F08A62", stroke_width=3).move_to(W(OX, OY))
        s_opt, focus = ValueTracker(0), ValueTracker(0)
        step = ValueTracker(0)
        v, w = DATA["cmd"]
        band_mob = always_redraw(lambda: band(snapshot(s_opt.get_value())[0], focus.get_value()))
        bot = always_redraw(lambda: turtlebot3_top(W, advance(pose0, v, w, step.get_value())))
        self.add(walls, path, goal, drum, band_mob, bot)
        self.wait(XFADE)  # Blender S1 dissolves into this frame

        # --- B02: forbidden zone (drum radius + robot radius + 0.20 m) ---
        limit = (OR + RR + MARGIN) * K
        halo = VGroup(*[Circle(radius=r, stroke_width=0, fill_color=P.error, fill_opacity=.055)
                        for r in np.linspace(OR * K, limit, 9)]).move_to(W(OX, OY))
        rim = DashedVMobject(Circle(radius=limit, color=P.error, stroke_width=2.5), num_dashes=48).move_to(W(OX, OY))
        with BeatClock(self, B02) as beat:
            beat.play(LaggedStart(*[GrowFromCenter(c) for c in halo], lag_ratio=.08), Create(rim),
                      self.camera.frame.animate.set(width=10.6).move_to(W(0.05, 0.10)), run_time=2.4)
            self.bring_to_front(drum, band_mob, bot)
            beat.wait(B02 * 0.55 - 2.4)  # "...그 한가운데를 지나갑니다"
            inside = [W(p[0], p[1]) for p in SNAP[0]["poses"] if clearance(p[0], p[1]) < MARGIN]
            beat.play(LaggedStart(*[Flash(pt, color=P.error, line_length=.18, flash_radius=.16) for pt in inside],
                                  lag_ratio=.12), run_time=1.4)

        # --- B03: cost J as a log-height stacked bar; optimisation collapses the obstacle share ---
        bar_x, bar_floor, bar_h, bar_w = 4.55, -2.15, 3.9, .5
        j0 = SNAP[0]["objective"]
        grow = ValueTracker(0)

        def bar_parts():
            _, _, c, j = snapshot(s_opt.get_value())
            h = bar_h * math.log10(1 + j) / math.log10(1 + j0) * grow.get_value()
            total = sum(c.values())
            y, rects = bar_floor, {}
            for k, col, _ in COSTS:
                hh = h * c[k] / total
                rects[k] = Rectangle(width=bar_w, height=max(hh, 1e-4), fill_color=col, fill_opacity=.92,
                                     stroke_width=0).move_to([bar_x, y + hh / 2, 0])
                y += hh
            return rects, y, j

        bar = always_redraw(lambda: VGroup(*bar_parts()[0].values()))
        base = Line([bar_x - .45, bar_floor, 0], [bar_x + .45, bar_floor, 0], color=P.muted, stroke_width=2)
        j_value = always_redraw(lambda: VGroup(
            MathTex("J", color=P.fg, font_size=46),
            DecimalNumber(bar_parts()[2], num_decimal_places=2, font_size=36, color=P.fg)
        ).arrange(DOWN, buff=.12).next_to([bar_x, bar_parts()[1], 0], UP, buff=.22).set_opacity(grow.get_value()))

        def tag(key, text, color):
            def build():
                r = bar_parts()[0][key]
                op = float(np.clip(r.height / .35, 0, 1)) * grow.get_value()
                return Text(text, font="NanumGothic", font_size=24, color=color).next_to(r, LEFT, buff=.18).set_opacity(op)
            return always_redraw(build)

        tags = VGroup(*[tag(k, t, c) for k, c, t in COSTS if t])
        self.add(base, bar, j_value, tags)
        with BeatClock(self, B03) as beat:
            beat.play(grow.animate.set_value(1), FadeIn(base), run_time=1.0)
            beat.play(s_opt.animate.set_value(CONVERGED), run_time=max(B03 - 2.2, 4.0), rate_func=smooth)

        # --- B04: the band carries time; a ghost follows the optimised dT schedule ---
        poses, dts, _, _ = snapshot(CONVERGED)
        cum = np.concatenate([[0], np.cumsum(dts)])
        tau = ValueTracker(0)

        def ghost_pose(t):
            i = int(np.clip(np.searchsorted(cum, t, side="right") - 1, 0, len(dts) - 1))
            f = (t - cum[i]) / dts[i]
            return (1 - f) * poses[i] + f * poses[i + 1]

        ghost = always_redraw(lambda: turtlebot3_top(W, ghost_pose(tau.get_value()), opacity=.55))
        clock = always_redraw(lambda: VGroup(
            MathTex("t", "=", color=P.fg, font_size=36),
            DecimalNumber(tau.get_value(), num_decimal_places=2, font_size=34, color=P.fg),
            MathTex(r"\mathrm{s}", color=P.muted, font_size=34),
        ).arrange(RIGHT, buff=.1).next_to(W(*ghost_pose(tau.get_value())[:2]), UP, buff=.55))
        total = MathTex(r"\textstyle\sum \Delta T", "=", f"{cum[-1]:.2f}", r"\,\mathrm{s}", font_size=38, color=P.fg)
        total.next_to(W(*poses[-1][:2]), UP, buff=1.0).shift(LEFT * .3)
        with BeatClock(self, B04) as beat:
            beat.wait(0.8)
            self.add(ghost, clock)
            beat.play(tau.animate.set_value(cum[-1]), run_time=cum[-1], rate_func=linear)  # real time
            beat.play(ReplacementTransform(clock, total), FadeOut(ghost), run_time=.6)

        # --- B05: only the first segment is executed (0.2 s shown in slow motion) ---
        with BeatClock(self, B05) as beat:
            beat.play(FadeOut(total), focus.animate.set_value(1), run_time=1.0)
            beat.play(step.animate.set_value(DATA["control_dt"]), run_time=min(2.6, B05 - 1.4), rate_func=smooth)

        # --- B06: pull back to the whole corridor for the cut to the full drive (S3) ---
        with BeatClock(self, B06) as beat:
            beat.play(self.camera.frame.animate.set(width=8.0 * K).move_to(W(0, 0)),
                      FadeOut(VGroup(bar, base, j_value, tags)), run_time=3.0)
