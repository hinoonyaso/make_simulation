"""Small data-driven Manim renderer for the current executable mechanism pilots."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, P


def text(value, size=24, color=P.fg, width=None):
    mob = txt(str(value), size=size, color=color)
    if width and mob.width > width:
        mob.scale_to_fit_width(width)
    return mob


def polyline(points, color, width=3):
    line = VMobject(color=color, stroke_width=width)
    return line.set_points_as_corners([np.array(point, dtype=float) for point in points])


def flat_values(value):
    return np.asarray(value, dtype=float).reshape(-1)[:12]


class MechanismTraceScene(Scene):
    def construct(self):
        apply_theme(self)
        plan_path = Path(os.environ["V11_VISUAL_PLAN"])
        manifest_path = Path(os.environ["V11_VISUAL_MANIFEST"])
        self.plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        beats = self.manifest["beats"]
        self.add(text(self.plan["title"], 34, P.fg, 13.2).to_edge(UP, buff=.35))
        graphic, transitions = self._build_graphic()
        for index, beat in enumerate(beats):
            duration = float(beat["sec"])
            caption = text(beat["caption"], 20, P.muted, 12.5).move_to([0, -3.1, 0])
            header = text(f"{index+1:02d} / {len(beats):02d}", 16, P.active).to_corner(UR, buff=.4)
            anims = [FadeIn(header), FadeIn(caption)]
            if index == 0:
                anims.extend(transitions[0])
            else:
                anims.extend(transitions[index])
            run_time = min(.6, duration * .35)
            self.play(*anims, run_time=run_time)
            self.wait(max(0.0, duration - run_time))
            self.remove(header, caption)

    def _build_graphic(self):
        kind = self.plan["kind"]
        if kind == "quantization": return self._quantization()
        if kind == "nms": return self._nms()
        if kind == "mcu_pid": return self._pid()
        if kind == "mujoco_arm": return self._mujoco_arm()
        raise ValueError(f"no Manim visual plan for mechanism: {kind}")

    def _quantization(self):
        p = self.plan
        original, quantized, restored = (flat_values(p[key]) for key in ("original", "quantized", "dequantized"))
        x0, x1, y = -5.4, 5.4, .25
        axis = Line([x0, y, 0], [x1, y, 0], color=P.faint)
        axis_labels = VGroup(text("실수 가중치", 18, P.muted).move_to([-4.5, 1.3, 0]),
                             text(f"{p['bits']}비트 정수 코드", 18, P.active).move_to([0, 1.3, 0]),
                             text("복원값과 오차", 18, P.result).move_to([4.5, 1.3, 0]))
        positions = np.linspace(x0 + .6, x1 - .6, len(original))
        original_dots = VGroup()
        quant_dots = VGroup()
        restored_dots = VGroup()
        value_labels = VGroup()
        for i, (value, q, deq, x) in enumerate(zip(original, quantized, restored, positions)):
            y0 = y + float(value) * 1.15
            yq = y + float(q) / max(1, 2**(p["bits"]-1)-1) * 1.15
            yd = y + float(deq) * 1.15
            original_dots.add(Dot([x, y0, 0], radius=.075, color=P.muted))
            quant_dots.add(Square(.15, color=P.active, fill_opacity=.8).move_to([x, yq, 0]))
            restored_dots.add(Dot([x, yd, 0], radius=.07, color=P.result))
            value_labels.add(text(f"{value:.2f}", 13, P.fg).move_to([x, -1.25, 0]))
        scale_label = text(f"scale={np.asarray(p['scale']).reshape(-1)[0]:.5g}   zero point={np.asarray(p['zero_point']).reshape(-1)[0]:g}",
                           21, P.active).move_to([0, 2.1, 0])
        error_text = f"가중치 최대 절대 오차 = {p['max_absolute_error']:.5g}"
        if p.get("activation_max_absolute_error") is not None:
            error_text += f"   활성값 최대 오차 = {p['activation_max_absolute_error']:.5g}"
        error_label = text(error_text, 18 if p.get("activation_max_absolute_error") is not None else 21,
                           P.result, 12.5).move_to([0, -2.15, 0])
        graphic = VGroup(axis, axis_labels, original_dots, quant_dots, restored_dots, value_labels,
                         scale_label, error_label)
        quant_dots.set_opacity(0); restored_dots.set_opacity(0); error_label.set_opacity(0)
        return graphic, [[Create(axis), FadeIn(axis_labels), FadeIn(original_dots), FadeIn(value_labels)],
                         [FadeIn(quant_dots), FadeIn(scale_label)],
                         [FadeIn(restored_dots), FadeIn(error_label)]]

    def _nms(self):
        p = self.plan
        boxes = np.asarray(p["boxes_xyxy"], dtype=float)
        lo, hi = boxes[:, :2].min(axis=0), boxes[:, 2:].max(axis=0)
        span = np.maximum(hi - lo, 1.0)
        canvas = Rectangle(width=7.8, height=4.0, color=P.faint).move_to([-2.3, -.1, 0])
        palette = [P.sensor, P.active, P.result, P.error, P.muted]
        candidates = VGroup()
        labels = VGroup()
        box_mobs = {}
        center = canvas.get_center()
        for i, (box, score, item_id) in enumerate(zip(boxes, p["scores"], p["ids"])):
            x1, y1 = (box[:2]-lo)/span
            x2, y2 = (box[2:]-lo)/span
            width, height = max(.18, (x2-x1)*6.8), max(.18, (y2-y1)*3.3)
            pos = [center[0]-3.4+(x1+x2)*3.4, center[1]+1.65-(y1+y2)*1.65, 0]
            color = palette[i % len(palette)]
            rect = Rectangle(width=width, height=height, color=color, stroke_width=3).move_to(pos)
            label = text(f"{item_id}  {score:.2f}", 15, color, 2.0).next_to(rect, UP, buff=.04)
            candidates.add(VGroup(rect, label)); box_mobs[item_id] = rect
            labels.add(label)
        threshold = text(f"confidence ≥ {p['confidence_threshold']:.2f}    IoU threshold = {p['iou_threshold']:.2f}",
                         20, P.muted).move_to([2.7, 2.3, 0])
        result = text("유지: " + ", ".join(p["kept_ids"]), 18, P.result, 6.2).move_to([2.7, -2.45, 0])
        result.set_opacity(0)
        graphic = VGroup(canvas, candidates, threshold, result)
        steps = p["steps"]
        selected = steps[0]["selected_id"] if steps else None
        pair = next((x for step in steps for x in step["comparisons"] if x["suppressed"]), None)
        compare_label = text((f"{selected} 선택 → {pair['candidate_id']}와 IoU {pair['iou']:.3f} 비교"
                              if pair else "실제 점수 순으로 후보를 비교"), 21, P.active, 8).move_to([2.5, -1.9, 0])
        graphic.add(compare_label)
        highlight = [Indicate(box_mobs[selected], color=P.active)] if selected in box_mobs else []
        return graphic, [[Create(canvas), FadeIn(threshold), FadeIn(candidates)],
                         [*highlight, FadeIn(compare_label)],
                         [*[mob.animate.set_stroke(color=P.result if item in p["kept_ids"] else P.muted)
                            for item, mob in box_mobs.items()], FadeIn(result)]]

    def _pid(self):
        p = self.plan
        rows = p["samples"]
        x0, y0, width, height = -5.1, -1.5, 8.2, 3.4
        axes = VGroup(Line([x0, y0, 0], [x0+width, y0, 0], color=P.faint),
                      Line([x0, y0, 0], [x0, y0+height, 0], color=P.faint))
        max_t = max(float(row["time_s"]) for row in rows) or 1.0
        max_speed = max(abs(float(p["target_rad_s"])), 1.0)
        step = max(1, len(rows)//100)
        sampled = rows[::step]
        measured = [[x0+width*row["time_s"]/max_t, y0+height*.5+height*.42*row["motor_speed_rad_s"]/max_speed, 0]
                    for row in sampled]
        encoder = [[x0+width*row["time_s"]/max_t, y0+height*.5+height*.42*row["encoder_speed_rad_s"]/max_speed, 0]
                   for row in sampled]
        reference_y = y0+height*.5+height*.42*p["target_rad_s"]/max_speed
        target = Line([x0, reference_y, 0], [x0+width, reference_y, 0], color=P.active, stroke_width=2)
        speed = polyline(measured, P.result, 4)
        encoder_line = polyline(encoder, P.sensor, 2)
        legend = VGroup(text("목표 속도", 17, P.active), text("모터 상태", 17, P.result),
                        text("엔코더 측정", 17, P.sensor)).arrange(RIGHT, buff=.5).move_to([1.0, 2.45, 0])
        pwm = [float(row["pwm_duty"]) for row in sampled]
        pwm_points = [[x0+width*i/max(1,len(pwm)-1), -2.5+float(value)*.42, 0]
                      for i, value in enumerate(pwm)]
        pwm_line = polyline(pwm_points, P.active, 3)
        label = text(f"이산 PID · 주기 {p['duration_s'] / max(1,len(rows)-1):.3f}s · PWM 범위 [-1, 1]",
                     16, P.muted).move_to([0, 1.95, 0])
        graphic = VGroup(axes, target, speed, encoder_line, legend, pwm_line, label)
        return graphic, [[Create(axes), Create(target), FadeIn(legend)],
                         [Create(speed), Create(encoder_line)], [Create(pwm_line), FadeIn(label)]]

    def _mujoco_arm(self):
        p = self.plan
        samples = p["samples"]
        names = p["joint_names"]
        shoulder_i = names.index("left_shoulder_pitch_joint")
        elbow_i = names.index("left_elbow_joint")
        x0, y0, width, height = -5, -1.5, 10, 3.4
        axes = VGroup(Line([x0, y0, 0], [x0+width, y0, 0], color=P.faint),
                      Line([x0, y0, 0], [x0, y0+height, 0], color=P.faint))
        max_t = max(row["t"] for row in samples) or 1.0
        def curve(index, color, offset):
            vals = [row["qpos"][index] for row in samples]
            scale = max(max(abs(v) for v in vals), .1)
            pts = [[x0+width*row["t"]/max_t, y0+height*.5+height*.4*(row["qpos"][index]/scale), 0]
                   for row in samples]
            return polyline(pts, color, 3)
        shoulder, elbow = curve(shoulder_i, P.sensor, 0), curve(elbow_i, P.result, 0)
        labels = VGroup(text("실제 MuJoCo 관절 상태", 20, P.fg),
                        text("어깨", 17, P.sensor), text("팔꿈치", 17, P.result)).arrange(RIGHT,buff=.5).move_to([0, 2.5, 0])
        ee_points = [[row["ee_pos"][0], row["ee_pos"][1], 0] for row in samples]
        xvals = [point[0] for point in ee_points]; yvals = [point[1] for point in ee_points]
        dx, dy = max(max(xvals)-min(xvals), 1e-3), max(max(yvals)-min(yvals), 1e-3)
        ee_line = polyline([[-4.5+9*(x-min(xvals))/dx, -1+2*(y-min(yvals))/dy, 0]
                            for x,y in zip(xvals,yvals)], P.active, 4)
        graphic=VGroup(axes,shoulder,elbow,labels,ee_line)
        return graphic, [[Create(axes), FadeIn(labels)], [Create(shoulder), Create(elbow)], [Create(ee_line)]]
