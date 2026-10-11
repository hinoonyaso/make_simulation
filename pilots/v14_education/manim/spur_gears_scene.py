"""Short Manim smoke scene for registered 20T:40T spur-gear education."""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, P
from core.education.gear_kinematics import external_spur_gear_kinematics, vertical_velocity_direction


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


def angular_direction_arrow(center, direction, color):
    """A small CCW/CW arrow; its sign is tied to the ideal angular velocity."""
    sign = 1 if direction > 0 else -1
    radius = .34
    start_angle = -.45
    sweep = sign * 1.65
    arc = Arc(radius=radius, start_angle=start_angle, angle=sweep, arc_center=center)
    arc.set_stroke(color, width=2.2)
    end_angle = start_angle + sweep
    tangent = sign * np.array([-np.sin(end_angle), np.cos(end_angle), 0.0])
    tip = Triangle().scale(.105).set_fill(color, opacity=1).set_stroke(color, width=0)
    tip.rotate(np.arctan2(tangent[1], tangent[0]) - PI / 2)
    endpoint = center + radius * np.array([np.cos(end_angle), np.sin(end_angle), 0.0])
    tip.move_to(endpoint - tangent * .045)
    return VGroup(arc, tip)


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
        nominal = external_spur_gear_kinematics(z1, z2, data["module_m"], 1.0)
        if not np.isclose(data["omega_2_over_omega_1"],
                          nominal["gear_angular_velocity_rad_s"]):
            raise ValueError("renderer context speed ratio does not match the registered gear asset")

        apply_theme(self)
        scale = 0.052  # scene units per millimetre, shared by pitch radii and center distance
        pitch_r1 = nominal["pinion_pitch_radius_m"] * 1000 * scale
        pitch_r2 = nominal["gear_pitch_radius_m"] * 1000 * scale
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
        pitch_guides = None
        phases = {row["phase_id"]: row for row in timeline["phases"]}
        for beat in manifest["beats"]:
            phase = phases[beat["phase_id"]]
            duration = (phase["presentation_end_frame"] - phase["presentation_start_frame"]) / timeline["fps"]
            if beat["phase_id"] == "gear_pair":
                intro = min(.75, duration * .25)
                self.play(FadeIn(title), FadeIn(parts), run_time=intro)
                self.wait(max(0, duration - intro))
            elif beat["phase_id"] == "opposite_direction":
                pitch_point = left_center + np.array([pitch_r1, 0.0, 0.0])
                pitch_circle1 = DashedVMobject(Circle(radius=pitch_r1).move_to(left_center),
                                               num_dashes=40).set_stroke(P.active, width=1.4, opacity=.9)
                pitch_circle2 = DashedVMobject(Circle(radius=pitch_r2).move_to(right_center),
                                               num_dashes=64).set_stroke(P.result, width=1.4, opacity=.9)
                point = Dot(pitch_point, radius=.07, color=P.fg)
                point_leader = Line(pitch_point + np.array([0, -.12, 0]),
                                    pitch_point + np.array([0, -.42, 0])).set_stroke(P.fg, width=1.2, opacity=.8)
                point_label = txt("P · 이상 피치점", 18, P.fg).move_to([-.75, -.82, 0])
                # At P, both ideal rolling velocities are equal and point along
                # the same common tangent even though omega_1 and omega_2 differ in sign.
                vt = nominal["pinion_pitch_velocity_m_s"]
                tangent_sign = vertical_velocity_direction(vt)
                if tangent_sign:
                    tangent_arrow = Arrow(pitch_point + np.array([.18, -.12 * tangent_sign, 0]),
                                          pitch_point + np.array([.18, .78 * tangent_sign, 0]),
                                          buff=0, color=P.result, stroke_width=4,
                                          max_tip_length_to_length_ratio=.28)
                    tangent_label = txt("vₜ₁ = vₜ₂", 20, P.fg).move_to([-1.0, -1.38 * tangent_sign, 0])
                else:
                    tangent_arrow = VGroup()
                    tangent_label = txt("vₜ₁ = vₜ₂ = 0", 19, P.fg).move_to([-1.0, -1.38, 0])
                angular1 = angular_direction_arrow(left_center, nominal["pinion_angular_velocity_rad_s"], P.active)
                angular2 = angular_direction_arrow(right_center, nominal["gear_angular_velocity_rad_s"], P.result)
                omega1_label = txt("ω₁", 18, P.fg).move_to(left_center + np.array([-.48, -.22, 0]))
                omega2_label = txt("ω₂", 18, P.fg).move_to(right_center + np.array([-.48, -.22, 0]))
                causal_note = txt("같은 접선 속도를 유지하려면 각속도는 반대 방향", 19, P.fg)
                causal_note.move_to([0, -2.03, 0])
                pitch_guides = VGroup(pitch_circle1, pitch_circle2, point, point_leader, point_label,
                                      tangent_arrow, tangent_label, angular1, angular2,
                                      omega1_label, omega2_label, causal_note)
                intro = min(.5, duration * .18)
                self.play(Create(pitch_circle1), Create(pitch_circle2), FadeIn(point),
                          FadeIn(point_label), FadeIn(tangent_arrow), FadeIn(tangent_label),
                          Create(angular1), Create(angular2), FadeIn(omega1_label),
                          FadeIn(omega2_label), FadeIn(causal_note), run_time=intro)
                rotate_pair(self, driver, driven, left_center, right_center,
                            data["omega_2_over_omega_1"], .5, max(.05, duration - intro))
            elif beat["phase_id"] == "speed_ratio":
                formula = txt(f"ω₂ / ω₁ = −Z₁ / Z₂ = {data['omega_2_over_omega_1']:.1f}", 26, P.fg)
                formula.move_to([0, -2.25, 0])
                intro = min(.4, duration * .18)
                animations = [FadeIn(formula)]
                if pitch_guides is not None:
                    animations.append(FadeOut(pitch_guides))
                self.play(*animations, run_time=intro)
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
