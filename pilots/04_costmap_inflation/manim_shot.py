"""Trace-backed view of the custom static costmap from topic 08."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from manim import *

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import P, BeatClock, beat_seconds, world_window  # noqa: E402

TRACE = json.loads((HERE / "data/costmap_trace.json").read_text(encoding="utf-8"))
SAMPLE = TRACE["samples"][0]
COST = np.asarray(SAMPLE["costmap"], dtype=float)
PATH = SAMPLE["path"]
DRUM = "#D9542C"
MAP_W = 8.4
MAP_CENTER = (2.65, 0.05)
W = world_window(15.5, MAP_CENTER)


def label(text, size=30, color=None, bold=False):
    return Text(text, font="NanumGothic", font_size=size, color=color or P.fg,
                weight=BOLD if bold else NORMAL)


def heat_image(mode):
    """Rasterize values directly from the recorded matrix; alpha reveals the cost state."""
    arr = COST[::-1, :]
    rgba = np.zeros((*arr.shape, 4), dtype=np.uint8)
    if mode == "lethal":
        mask = arr >= 255
        rgba[mask] = (239, 68, 68, 235)
    elif mode == "graded":
        positive = (arr > 0) & (arr < 255)
        t = np.clip(arr / 180.0, 0, 1)
        rgba[..., 0] = 255
        rgba[..., 1] = (190 * (1 - t)).astype(np.uint8)
        rgba[..., 2] = (35 * (1 - t)).astype(np.uint8)
        rgba[..., 3] = np.where(positive, np.clip(65 + 155 * t, 0, 220), 0).astype(np.uint8)
        rgba[arr >= 255] = (239, 68, 68, 235)
    display_w = len(TRACE["xs_m"]) * TRACE["resolution_m"] * W.k
    display_h = len(TRACE["ys_m"]) * TRACE["resolution_m"] * W.k
    px_w = round(display_w * config.pixel_width / config.frame_width)
    px_h = round(display_h * config.pixel_height / config.frame_height)
    rgba = np.asarray(Image.fromarray(rgba).resize((px_w, px_h), Image.Resampling.NEAREST))
    image = ImageMobject(rgba).scale_to_fit_width(display_w)
    image.move_to(W((TRACE["xs_m"][0] + TRACE["xs_m"][-1]) / 2,
                    (TRACE["ys_m"][0] + TRACE["ys_m"][-1]) / 2))
    return image


def map_base():
    xmin, ymin = TRACE["xs_m"][0], TRACE["ys_m"][0]
    xmax, ymax = TRACE["xs_m"][-1], TRACE["ys_m"][-1]
    floor = Rectangle(width=(xmax-xmin+TRACE["resolution_m"])*W.k,
                      height=(ymax-ymin+TRACE["resolution_m"])*W.k,
                      stroke_color="#64748B", stroke_width=2,
                      fill_color="#111827", fill_opacity=1)
    floor.move_to(W((xmin+xmax)/2, (ymin+ymax)/2))
    obstacles = VGroup()
    for x0, y0, x1, y1 in TRACE["obstacle_boxes_m"]:
        box = Rectangle(width=(x1-x0)*W.k, height=(y1-y0)*W.k,
                        stroke_color="#A8B0BC", stroke_width=1.5,
                        fill_color="#687385", fill_opacity=.88)
        box.move_to(W((x0+x1)/2, (y0+y1)/2))
        obstacles.add(box)
    boundary = Rectangle(width=9*W.k, height=6*W.k, stroke_color="#64748B", stroke_width=2)
    boundary.move_to(W(0,0))
    return VGroup(floor, boundary, obstacles)


def grid_lines():
    """Fine cell boundaries keep the 0.15 m source discretization readable."""
    dx = dy = TRACE["resolution_m"]
    xmin, ymin = TRACE["xs_m"][0] - dx / 2, TRACE["ys_m"][0] - dy / 2
    xmax, ymax = TRACE["xs_m"][-1] + dx / 2, TRACE["ys_m"][-1] + dy / 2
    lines = VGroup()
    for i in range(len(TRACE["xs_m"]) + 1):
        x = xmin + i * dx
        lines.add(Line(W(x, ymin), W(x, ymax), color="#718096", stroke_width=.65, stroke_opacity=.28))
    for i in range(len(TRACE["ys_m"]) + 1):
        y = ymin + i * dy
        lines.add(Line(W(xmin, y), W(xmax, y), color="#718096", stroke_width=.65, stroke_opacity=.28))
    return lines


def path_line():
    return VMobject(color="#F8FAFC", stroke_width=5, stroke_opacity=.95).set_points_as_corners(
        [W(float(x), float(y)) for x, y in PATH])


class CostmapInflation(MovingCameraScene):
    def construct(self):
        self.camera.background_color = P.bg
        b2,b3,b4,b5,b6 = beat_seconds(HERE / "visual_manifest.json", "B02", "B03", "B04", "B05", "B06")
        title = label("장애물 주변 비용장", 40, bold=True).to_edge(UP, buff=.36)
        base = map_base()
        cells = grid_lines()
        none = heat_image("none")
        lethal = heat_image("lethal")
        graded = heat_image("graded")
        note = label("교육용 정적 costmap · 셀 간격 0.15 m", 22, P.muted).next_to(title, DOWN, buff=.06)
        # B02: reveal the exact trace grid over the shared world geometry.
        intro_label = label("장애물까지의 거리 → 칸마다 비용", 24, P.sensor).move_to([4.35, 1.45, 0])
        with BeatClock(self, b2) as beat:
            self.add(base, none, cells, title, note)
            beat.play(FadeIn(intro_label), run_time=.7)
        # B03: the model's forbidden band is derived from robot radius + 0.22 m.
        caption = label("255  통과 금지", 31, P.error, bold=True).move_to([3.4, 1.38, 0])
        eq1 = MathTex(r"d \leq r_{robot} + 0.22\,m", font_size=37, color=P.fg).move_to([3.45, .52, 0])
        with BeatClock(self, b3) as beat:
            beat.play(Transform(none, lethal), FadeOut(intro_label), run_time=1.0)
            self.add(caption, eq1)
            beat.wait(.5)
        # B04: reveal the graded halo while preserving the obstacle and lethal geometry.
        label4 = label("가까울수록 비용 증가", 29, P.active, bold=True).move_to([3.55, 1.45, 0])
        eq2 = MathTex(r"180\,e^{-3.5\,\max(d-0.25,\,0)}", font_size=32, color=P.active).move_to([3.55, .55, 0])
        range_note = label("d < 1 m 에서 감소", 24, P.muted).move_to([3.55, -.16, 0])
        with BeatClock(self, b4) as beat:
            beat.play(Transform(none, graded), FadeOut(caption), FadeOut(eq1), run_time=1.0)
            beat.play(FadeIn(label4), FadeIn(eq2), FadeIn(range_note), run_time=.7)
        # B05: the baseline route is a source path over the same costmap.
        route = path_line()
        route_label = label("기록된 전역 경로", 25, P.fg, bold=True).move_to([4.35, 1.45, 0])
        with BeatClock(self, b5) as beat:
            beat.play(FadeOut(label4), FadeOut(eq2), FadeOut(range_note), run_time=.35)
            beat.play(Create(route), run_time=2.1)
            beat.play(FadeIn(route_label), run_time=.45)
        # B06: clarify the evidence boundary; this is not an executed Nav2 layer.
        disclaimer = label("topics/08 교육용 모델", 24, P.sensor, bold=True).move_to([4.35, 1.35, 0])
        disclaimer2 = label("실제 Nav2 인플레이션 레이어\n실행은 아닙니다", 21, P.fg).move_to([4.35, .52, 0])
        with BeatClock(self, b6) as beat:
            beat.play(FadeOut(route_label), run_time=.3)
            beat.play(FadeIn(disclaimer), FadeIn(disclaimer2), run_time=.6)
            beat.wait(.8)


if __name__ == "__main__":
    config.pixel_width, config.pixel_height, config.frame_rate = 1920, 1080, 30
