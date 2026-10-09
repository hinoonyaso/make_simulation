"""Animate the actual recorded MuJoCo arm and joint trace; no invented poses."""
from pathlib import Path
import json
import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys_path = ROOT / "core/manim-robotics-education-skill/templates"
import sys
sys.path.insert(0, str(sys_path))
from manim_kit import apply_theme, txt, P

TRACE = json.loads((HERE / "data/trace.json").read_text(encoding="utf-8"))
SAMPLES = TRACE["samples"]
TIMES = np.asarray([sample["t"] for sample in SAMPLES])
JOINTS = TRACE["model"]["joint_names_in_qpos_order"]
SHOULDER_INDEX = JOINTS.index("left_shoulder_pitch_joint")
ACTUAL = np.asarray([sample["qpos"][SHOULDER_INDEX] for sample in SAMPLES])
TARGET = np.asarray([sample["target"][0] for sample in SAMPLES])


def scene_pos(position):
    # Side-on x-z projection of the recorded MuJoCo world coordinate.
    return np.array([-3.35 + position[0] * 5.2,
                     1.15 + (position[2] - 1.53) * 5.2, 0.0])


def sample_at(index, key):
    i = min(len(SAMPLES) - 1, max(0, int(round(index))))
    return SAMPLES[i][key]


class MujocoArmTraceScene(Scene):
    def construct(self):
        apply_theme(self)
        title = txt("토크가 관절을 움직이고, 손 위치가 바뀐다", 38, P.fg).move_to([0, 3.25, 0])
        model_note = txt("MuJoCo 물리 trace · Unitree H1 · 고정 골반 · 실제 형상 메시는 표시하지 않음",
                         19, P.muted).move_to([0, 2.78, 0])
        self.add(title, model_note)

        samples = SAMPLES
        shoulder = scene_pos(samples[0]["shoulder_pos"])
        elbow0 = scene_pos(samples[0]["elbow_pos"])
        hand0 = scene_pos(samples[0]["ee_pos"])
        upper_arm = Line(shoulder, elbow0, color=P.sensor, stroke_width=12)
        forearm = Line(elbow0, hand0, color=P.result, stroke_width=10)
        shoulder_dot = Dot(shoulder, radius=.12, color=P.sensor)
        elbow_dot = Dot(elbow0, radius=.13, color=P.active)
        hand_dot = Dot(hand0, radius=.16, color=P.result)
        arm_label = txt("실제 body pose를 잇는 trace 재생", 19, P.muted).move_to([-2.1, -2.15, 0])

        def update_upper(mob):
            i = min(len(samples) - 1, max(0, round(playhead.get_value())))
            mob.put_start_and_end_on(scene_pos(samples[i]["shoulder_pos"]),
                                     scene_pos(samples[i]["elbow_pos"]))

        def update_fore(mob):
            i = min(len(samples) - 1, max(0, round(playhead.get_value())))
            mob.put_start_and_end_on(scene_pos(samples[i]["elbow_pos"]),
                                     scene_pos(samples[i]["ee_pos"]))

        upper_arm.add_updater(update_upper)
        forearm.add_updater(update_fore)
        elbow_dot.add_updater(lambda mob: mob.move_to(scene_pos(
            sample_at(playhead.get_value(), "elbow_pos"))))
        hand_dot.add_updater(lambda mob: mob.move_to(scene_pos(
            sample_at(playhead.get_value(), "ee_pos"))))

        x_values = TIMES.tolist()
        axes = Axes(x_range=[0, float(TIMES[-1]), .5], y_range=[-.1, .6, .1],
                    x_length=5.1, y_length=3.5,
                    axis_config={"color": P.faint, "include_numbers": True,
                                 "font_size": 17}, tips=False).move_to([2.25, .15, 0])
        target_line = axes.plot_line_graph(x_values, TARGET.tolist(),
                                           add_vertex_dots=False, line_color=P.active,
                                           stroke_width=3)
        actual_line = axes.plot_line_graph(x_values, ACTUAL.tolist(),
                                           add_vertex_dots=False, line_color=P.result,
                                           stroke_width=3)
        graph_title = txt("왼쪽 어깨 관절각", 23, P.fg).move_to([2.25, 2.2, 0])
        target_key = txt("목표", 17, P.active).move_to([.55, 1.88, 0])
        actual_key = txt("실제", 17, P.result).move_to([1.35, 1.88, 0])
        target_dot = Dot(axes.c2p(0, TARGET[0]), radius=.07, color=P.active)
        actual_dot = Dot(axes.c2p(0, ACTUAL[0]), radius=.07, color=P.result)
        playhead = ValueTracker(0)
        target_dot.add_updater(lambda mob: mob.move_to(axes.c2p(
            TIMES[min(len(TIMES)-1, round(playhead.get_value()))],
            TARGET[min(len(TARGET)-1, round(playhead.get_value()))])))
        actual_dot.add_updater(lambda mob: mob.move_to(axes.c2p(
            TIMES[min(len(TIMES)-1, round(playhead.get_value()))],
            ACTUAL[min(len(ACTUAL)-1, round(playhead.get_value()))])))

        time_read = DecimalNumber(0, num_decimal_places=2, font_size=24, color=P.fg)
        time_label = txt("시뮬레이션 t =", 20, P.muted)
        time_group = VGroup(time_label, time_read).arrange(RIGHT, buff=.12).move_to([0, -2.75, 0])
        time_read.add_updater(lambda mob: mob.set_value(
            TIMES[min(len(TIMES)-1, round(playhead.get_value()))]))
        self.add(upper_arm, forearm, shoulder_dot, elbow_dot, hand_dot,
                 arm_label, axes, target_line, actual_line, graph_title,
                 target_key, actual_key, target_dot, actual_dot, time_group)
        self.wait(.6)
        self.play(playhead.animate.set_value(len(samples) - 1),
                  run_time=8.0, rate_func=linear)
        upper_arm.clear_updaters(); forearm.clear_updaters()
        elbow_dot.clear_updaters(); hand_dot.clear_updaters()
        target_dot.clear_updaters(); actual_dot.clear_updaters(); time_read.clear_updaters()
        self.wait(1.2)
