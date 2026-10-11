"""Render PyBaMM result samples as a voltage trace and result-boundary summary."""
from __future__ import annotations

import csv
import hashlib
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


def load_samples(context: dict, context_path: Path) -> dict[str, np.ndarray]:
    info = context.get("solver_result")
    if not info or info.get("solver_id") != "pybamm":
        raise ValueError("Battery Manim renderer requires a validated PyBaMM result contract")
    path = context_path.parent / info["timeseries_file"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != info.get("result_sha256"):
        raise ValueError("Battery Manim result CSV SHA-256 does not match the validated solver contract")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    fields = ("time_s", "terminal_voltage_v", "current_a", "discharge_capacity_ah", "estimated_soc")
    data = {key: np.asarray([float(row[key]) for row in rows], dtype=float) for key in fields}
    if len(data["time_s"]) < 2 or data["time_s"][0] != 0 or np.any(np.diff(data["time_s"]) <= 0):
        raise ValueError("Battery Manim result timestamps are invalid")
    if data["time_s"][-1] != float(info["actual_end_time_s"]):
        raise ValueError("Battery Manim result range does not match solver provenance")
    if len(data["time_s"]) != int(info["sample_count"]):
        raise ValueError("Battery Manim sample count does not match solver provenance")
    return data


class BatteryLessonScene(Scene):
    def construct(self):
        manifest_path = Path(os.environ["EDUCATION_MANIFEST_PATH"])
        timeline_path = Path(os.environ["EDUCATION_TIMELINE_PATH"])
        context_path = Path(os.environ["EDUCATION_RENDER_CONTEXT_PATH"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        context = json.loads(context_path.read_text(encoding="utf-8"))
        data = load_samples(context, context_path)
        solver = context["solver_result"]
        result = json.loads((context_path.parent / solver["result_file"]).read_text(encoding="utf-8"))
        fps = int(timeline["fps"])
        phases = {row["phase_id"]: row for row in timeline["phases"]}
        apply_theme(self)

        for beat in manifest["beats"]:
            phase = phases[beat["phase_id"]]
            frames = phase["presentation_end_frame"] - phase["presentation_start_frame"]
            duration = frames / fps
            if beat.get("tool") == "B":
                # Blender owns this timeline slice in the final composition.
                # Fade any Manim state here so it cannot leak into a later
                # Manim slice, while preserving the shared phase duration.
                fade_time = min(.25, duration) if self.mobjects else 0.0
                if fade_time:
                    self.play(*(FadeOut(mob) for mob in list(self.mobjects)), run_time=fade_time)
                self.wait(duration - fade_time)
                continue

            # Create a fresh title for each Manim-owned phase. FadeOut mutates
            # the previous phase's mobjects, so reusing its title can preserve
            # a zero-opacity state after an intervening Blender phase.
            title = txt(manifest.get("title", "배터리 방전 Solver 결과"), 28, P.fg).to_edge(UP, buff=.28)

            if beat["phase_id"] == "voltage_curve":
                xmin, xmax = 0.0, float(data["time_s"][-1] / 60)
                ymin = float(np.floor(data["terminal_voltage_v"].min() * 2) / 2 - .25)
                ymax = float(np.ceil(data["terminal_voltage_v"].max() * 2) / 2 + .25)
                graph_left, graph_right = -5.05, 5.25
                graph_bottom, graph_top = -2.15, 1.65

                def point(t_min: float, voltage: float) -> np.ndarray:
                    x = graph_left + (t_min - xmin) / (xmax - xmin) * (graph_right - graph_left)
                    y = graph_bottom + (voltage - ymin) / (ymax - ymin) * (graph_top - graph_bottom)
                    return np.array([x, y, 0.0])

                axes = VGroup(
                    Line([graph_left, graph_bottom, 0], [graph_right, graph_bottom, 0], color=P.muted, stroke_width=1.4),
                    Line([graph_left, graph_bottom, 0], [graph_left, graph_top, 0], color=P.muted, stroke_width=1.4),
                )
                x_label = txt("시간 [분]", 18, P.muted).next_to(axes[0], DOWN, buff=.16)
                y_label = txt("단자 전압 [V]", 18, P.muted).rotate(PI / 2).move_to([-6.35, (graph_bottom + graph_top) / 2, 0])
                x_ticks = VGroup()
                for value in np.linspace(xmin, xmax, 4):
                    p = point(value, ymin)
                    x_ticks.add(Line(p, p + DOWN * .07, color=P.muted, stroke_width=1))
                    x_ticks.add(txt(f"{value:.0f}", 14, P.muted).next_to(p, DOWN, buff=.10))
                y_ticks = VGroup()
                for value in np.linspace(ymin, ymax, 3):
                    p = point(xmin, value)
                    y_ticks.add(Line(p, p + LEFT * .07, color=P.muted, stroke_width=1))
                    y_ticks.add(txt(f"{value:.1f}", 14, P.muted).next_to(p, LEFT, buff=.10))
                times_min = data["time_s"] / 60
                curve = VMobject().set_points_as_corners([
                    point(float(x), float(y)) for x, y in zip(times_min, data["terminal_voltage_v"])
                ]).set_stroke(P.active, width=3.0)
                progress = ValueTracker(0.0)
                def sample_at_progress() -> tuple[float, float, float]:
                    solver_time = float(progress.get_value()) * float(data["time_s"][-1])
                    volts = float(np.interp(solver_time, data["time_s"], data["terminal_voltage_v"]))
                    soc = float(np.interp(solver_time, data["time_s"], data["estimated_soc"]))
                    return solver_time, volts, soc
                cursor_dot = always_redraw(lambda: Dot(
                    point(sample_at_progress()[0] / 60, sample_at_progress()[1]), radius=.075, color=P.result))
                current_readout = always_redraw(lambda: txt(
                    f"{sample_at_progress()[1]:.2f} V", 25, P.result).move_to([3.9, 2.35, 0]))
                current_time = always_redraw(lambda: txt(
                    f"{sample_at_progress()[0] / 60:.1f} / {xmax:.0f} 분", 17, P.fg).move_to([3.75, -2.55, 0]))
                heading = txt("PyBaMM SPM 계산 · 저장된 전압 샘플", 19, P.fg).move_to([0, 2.35, 0])
                self.play(FadeIn(title), FadeIn(heading), FadeIn(axes), FadeIn(x_label), FadeIn(y_label),
                          FadeIn(x_ticks), FadeIn(y_ticks), run_time=min(1.0, duration / 4))
                self.play(Create(curve), run_time=min(1.0, duration / 4), rate_func=linear)
                self.add(cursor_dot, current_readout, current_time)
                self.play(progress.animate.set_value(1.0), run_time=duration - min(2.0, duration / 2), rate_func=linear)
                tail = duration - min(1.0, duration / 4) * 2 - (duration - min(2.0, duration / 2))
                if tail > 0:
                    self.wait(tail)
                self.remove(cursor_dot, current_readout, current_time)

            elif beat["phase_id"] == "model_limits":
                last_voltage = float(data["terminal_voltage_v"][-1])
                first_voltage = float(data["terminal_voltage_v"][0])
                first_soc = float(data["estimated_soc"][0])
                last_soc = float(data["estimated_soc"][-1])
                duration_per = duration / 3
                heading = txt("계산 조건과 결과의 경계", 25, P.fg).move_to([0, 2.45, 0])
                condition = txt(
                    f"SPM · Chen2020 · {result['discharge_c_rate']:.1f}C · 등온 · {result['actual_end_time_s'] / 60:.1f}분",
                    21, P.active).move_to([0, 1.45, 0])
                voltage = txt(f"전압  {first_voltage:.2f} V  →  {last_voltage:.2f} V", 24, P.fg).move_to([0, .35, 0])
                soc_line = txt(f"Coulomb Counting 추정 SOC  {first_soc * 100:.0f}%  →  {last_soc * 100:.0f}%",
                               21, P.result).move_to([0, -.45, 0])
                boundary1 = txt("미계산: 전해질 농도장 · 발열 · 노화", 18, P.muted).move_to([0, -1.5, 0])
                boundary2 = txt("추정 SOC는 실측값이나 BMS 상태가 아닙니다", 18, P.muted).move_to([0, -2.1, 0])
                self.play(FadeIn(title), FadeIn(heading), run_time=duration_per)
                self.play(FadeIn(condition), FadeIn(voltage), FadeIn(soc_line), run_time=duration_per)
                self.play(FadeIn(boundary1), FadeIn(boundary2), run_time=duration_per)
            else:
                raise ValueError(f"unsupported battery Manim phase {beat['phase_id']!r}")

        # Manim's movie writer can leave the terminal presentation frame black
        # when the last animation ends exactly on the scene boundary. Hold the
        # final state for one frame; the shared 720-frame timeline still crops
        # the same 24-second presentation range.
        self.wait(1 / fps)
