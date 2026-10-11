"""Short Manim smoke scene for registered 20T:40T spur-gear education."""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, P


def gear_outline(teeth: int, radius: float, *, center=(0.0, 0.0, 0.0), phase=0.0, color=BLUE):
    """Draw a schematic tooth-count polygon; it is not an involute tooth profile."""
    root = radius * .91
    points = []
    for tooth in range(teeth):
        base = phase + TAU * tooth / teeth
        for fraction, radial in ((-.40, root), (-.17, radius), (.17, radius), (.40, root)):
            angle = base + TAU * fraction / teeth
            points.append(np.array([center[0] + radial * np.cos(angle),
                                    center[1] + radial * np.sin(angle), center[2]]))
    shape = VMobject()
    shape.set_points_as_corners(points + [points[0]])
    shape.set_fill(color, opacity=.22)
    shape.set_stroke(color, width=2.4)
    return shape


def rotate_pair(scene, driver, driven, driver_center, driven_center, speed_ratio, turns, duration):
    """Advance both persistent gears from one angular-progress tracker."""
    progress = ValueTracker(0)
    driver_previous, driven_previous = [0.0], [0.0]

    def update_driver(mob):
        current = progress.get_value()
        mob.rotate(TAU * (current - driver_previous[0]), about_point=driver_center)
        driver_previous[0] = current

    def update_driven(mob):
        current = progress.get_value()
        mob.rotate(TAU * speed_ratio * (current - driven_previous[0]), about_point=driven_center)
        driven_previous[0] = current

    driver.add_updater(update_driver)
    driven.add_updater(update_driven)
    scene.play(progress.animate.set_value(turns), run_time=duration, rate_func=linear)
    driver.remove_updater(update_driver)
    driven.remove_updater(update_driven)


class SpurGearsLessonScene(Scene):
    def construct(self):
        manifest_path = Path(os.environ["EDUCATION_MANIFEST_PATH"])
        timeline_path = Path(os.environ["EDUCATION_TIMELINE_PATH"])
        context_path = Path(os.environ["EDUCATION_RENDER_CONTEXT_PATH"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        context = json.loads(context_path.read_text(encoding="utf-8"))
        data = context["calculated_results"]
        z1, z2 = data["pinion_teeth"], data["gear_teeth"]
        if not np.isclose(data["omega_2_over_omega_1"], -z1 / z2):
            raise ValueError("renderer context speed ratio does not match the registered gear asset")

        apply_theme(self)
        scale = 0.052  # scene units per millimetre, shared by pitch radii and center distance
        pitch_r1 = data["module_m"] * z1 * 500 * scale
        pitch_r2 = data["module_m"] * z2 * 500 * scale
        center_gap = data["center_distance_m"] * 1000 * scale
        left_center = np.array([-center_gap / 2, .35, 0.0])
        right_center = np.array([center_gap / 2, .35, 0.0])
        driver_shape = gear_outline(z1, pitch_r1, center=left_center, color=P.active)
        driven_shape = gear_outline(z2, pitch_r2, center=right_center,
                                    phase=PI / z2, color=P.result)
        driver_marker = Dot(left_center + np.array([0, pitch_r1 * .68, 0]), radius=.075, color=P.fg)
        driven_marker = Dot(right_center + np.array([0, pitch_r2 * .68, 0]), radius=.075, color=P.fg)
        driver = VGroup(driver_shape, driver_marker)
        driven = VGroup(driven_shape, driven_marker)
        c1, c2 = Dot(left_center, radius=.045, color=P.fg), Dot(right_center, radius=.045, color=P.fg)
        driver_label = txt(f"구동 · {z1}T", 23, P.active).move_to([-5.15, .35, 0])
        driven_label = txt(f"종동 · {z2}T", 23, P.result).move_to([5.15, .35, 0])
        title = txt(manifest.get("title", "기어의 회전 방향과 속도"), 29, P.fg).to_edge(UP, buff=.35)
        parts = VGroup(driver, driven, c1, c2, driver_label, driven_label)
        formula = None
        boundary = None
        phases = {row["phase_id"]: row for row in timeline["phases"]}
        for beat in manifest["beats"]:
            phase = phases[beat["phase_id"]]
            duration = (phase["presentation_end_frame"] - phase["presentation_start_frame"]) / timeline["fps"]
            if beat["phase_id"] == "gear_pair":
                intro = min(.75, duration * .25)
                self.play(FadeIn(title), FadeIn(parts), run_time=intro)
                self.wait(max(0, duration - intro))
            elif beat["phase_id"] == "opposite_direction":
                rotate_pair(self, driver, driven, left_center, right_center,
                            data["omega_2_over_omega_1"], .5, duration)
            elif beat["phase_id"] == "speed_ratio":
                formula = txt(f"ω₂ / ω₁ = −Z₁ / Z₂ = {data['omega_2_over_omega_1']:.1f}", 26, P.fg)
                formula.move_to([0, -2.25, 0])
                intro = min(.4, duration * .18)
                self.play(FadeIn(formula), run_time=intro)
                rotate_pair(self, driver, driven, left_center, right_center,
                            data["omega_2_over_omega_1"], .5, max(.05, duration - intro))
            elif beat["phase_id"] == "ideal_boundary":
                boundary = txt("이상적 속도 비 · 효율/응력/백래시는 미계산", 18, P.muted)
                boundary.move_to([0, -2.25, 0])
                intro = min(.5, duration * .2)
                if formula is not None:
                    self.play(FadeOut(formula), FadeIn(boundary), run_time=intro)
                else:
                    self.play(FadeIn(boundary), run_time=intro)
                self.wait(max(0, duration - intro))
            else:
                raise ValueError(f"SpurGearsLessonScene has no implementation for phase {beat['phase_id']!r}")
