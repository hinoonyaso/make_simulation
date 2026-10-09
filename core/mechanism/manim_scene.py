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
            state_animations = transitions[index] if index < len(transitions) else []
            anims.extend(state_animations)
            state_runtime = max([value for animation in state_animations
                                 if isinstance((value := getattr(animation, "run_time", .6)), (int, float))] + [.6])
            run_time = min(duration * .88, max(.6, state_runtime))
            self.play(*anims, run_time=run_time)
            self.wait(max(0.0, duration - run_time))
            self.remove(header, caption)

    def _build_graphic(self):
        kind = self.plan["kind"]
        if kind == "quantization": return self._quantization()
        if kind == "nms": return self._nms()
        if kind == "mcu_pid": return self._pid()
        if kind == "mujoco_arm": return self._mujoco_arm()
        if kind == "self_attention": return self._self_attention()
        raise ValueError(f"no Manim visual plan for mechanism: {kind}")

    def _quantization(self):
        p = self.plan
        original, quantized, restored = (flat_values(p[key]) for key in ("original", "quantized", "dequantized"))
        x0, x1, y = -5.4, 5.4, .25
        qmin, qmax = int(p["qmin"]), int(p["qmax"])
        real_low = min(float(np.min(original)), float(np.min(restored)), 0.0)
        real_high = max(float(np.max(original)), float(np.max(restored)), 0.0)
        def normalize(value, low, high):
            return 0.0 if high <= low else 2.0 * (float(value) - low) / (high - low) - 1.0
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
            y0 = y + normalize(value, real_low, real_high) * 1.15
            # Place the integer code on the same calibrated interval as its
            # dequantized real value; this makes zero_point's offset visible.
            yq = y + normalize(q, qmin, qmax) * 1.15
            yd = y + normalize(deq, real_low, real_high) * 1.15
            original_dots.add(Dot([x, y0, 0], radius=.075, color=P.muted))
            quant_dots.add(Square(.15, color=P.active, fill_opacity=.8).move_to([x, yq, 0]))
            restored_dots.add(Dot([x, yd, 0], radius=.07, color=P.result))
            value_labels.add(text(f"{value:.2f}", 13, P.fg).move_to([x, -1.25, 0]))
        scale_label = text(f"scale={np.asarray(p['scale']).reshape(-1)[0]:.5g}   zero point={np.asarray(p['zero_point']).reshape(-1)[0]:g}   code=[{qmin}, {qmax}]",
                           21, P.active).move_to([0, 2.1, 0])
        error_text = f"가중치 최대 절대 오차 = {p['max_absolute_error']:.5g}"
        if p.get("activation_max_absolute_error") is not None:
            error_text += f"   활성값 최대 오차 = {p['activation_max_absolute_error']:.5g}"
        error_label = text(error_text, 18 if p.get("activation_max_absolute_error") is not None else 21,
                           P.result, 12.5).move_to([0, -2.15, 0])
        graphic = VGroup(axis, axis_labels, original_dots, quant_dots, restored_dots, value_labels,
                         scale_label, error_label)
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
        comparison_label = text("confidence 통과 후보를 점수 순서로 비교", 17, P.active, 5.0).move_to([3.55, .3, 0])
        graphic = VGroup(canvas, candidates, threshold, result, comparison_label)
        steps = p["steps"]
        comparisons = []
        for step in steps:
            winner = step["selected_id"]
            if winner in box_mobs:
                comparisons.append(Indicate(box_mobs[winner], color=P.active, scale_factor=1.05))
            for item in step["comparisons"]:
                candidate = item["candidate_id"]
                if candidate not in box_mobs: continue
                decision = "억제" if item["suppressed"] else "유지"
                label = text(f"{winner} × {candidate}\nIoU {item['iou']:.3f} → {decision}",
                             18, P.error if item["suppressed"] else P.result, 4.8).move_to([3.55, .3, 0])
                comparisons.extend([Indicate(box_mobs[candidate], color=P.error if item["suppressed"] else P.result),
                                    Transform(comparison_label, label), Wait(.16)])
        if comparisons:
            comparisons.insert(0, FadeIn(comparison_label))
        comparison_sequence = Succession(*comparisons).set_run_time(3.3) if comparisons else Wait(.1)
        return graphic, [[Create(canvas), FadeIn(threshold), FadeIn(candidates)],
                         [comparison_sequence],
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
        time_cursor = ValueTracker(0.0)
        cursor = always_redraw(lambda: Line(
            [x0+width*time_cursor.get_value()/max_t, y0-.12, 0],
            [x0+width*time_cursor.get_value()/max_t, y0+height+.12, 0],
            color=P.active, stroke_width=2))
        label = text(f"이산 PID · 주기 {p['duration_s'] / max(1,len(rows)-1):.3f}s · PWM 범위 [-1, 1]",
                     16, P.muted).move_to([0, 1.95, 0])
        graphic = VGroup(axes, target, speed, encoder_line, legend, pwm_line, label, cursor)
        return graphic, [[Create(axes), Create(target), FadeIn(legend)],
                         [Create(speed).set_run_time(2.6), Create(encoder_line).set_run_time(2.6),
                          FadeIn(cursor), time_cursor.animate.set_value(max_t).set_run_time(2.6)],
                         [Create(pwm_line), FadeIn(label)]]

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

    def _self_attention(self):
        p = self.plan
        n = len(p["tokens"])
        def matrix(values, title, color):
            values = np.asarray(values, dtype=float)
            group = VGroup()
            for row in range(values.shape[0]):
                for col in range(values.shape[1]):
                    value = float(values[row, col])
                    cell = Square(.78, color=color, stroke_width=1.4,
                                  fill_opacity=.12 + .65 * min(1.0, abs(value)))
                    cell.move_to([-.39*(values.shape[1]-1)+col*.82,
                                  .39*(values.shape[0]-1)-row*.82, 0])
                    label = text(f"{value:.2f}", 15, P.fg).move_to(cell)
                    group.add(VGroup(cell, label))
            title_mob = text(title, 23, color, 10).move_to([0, 2.25, 0])
            row_tags = VGroup(*[text(f"Q{i+1}", 14, P.muted).move_to([-2.2, .39*(n-1)-i*.82, 0]) for i in range(n)])
            col_tags = VGroup(*[text(f"K{i+1}", 14, P.muted).move_to([-.39*(n-1)+i*.82, 1.45, 0]) for i in range(n)])
            return VGroup(title_mob, row_tags, col_tags, group)
        raw = matrix(p["raw_scores"], "질문 Q × 키 Kᵀ : 내적 점수", P.active)
        scaled = matrix(p["scaled_scores"], f"차원으로 나눈 점수 · ÷ {p['scale_factor']:.2f}", P.sensor)
        weights = matrix(p["attention_weights"], "행마다 정규화한 softmax 가중치", P.result)
        raw_title, row_tags, col_tags, score_cells = raw.submobjects
        scaled_title, _, _, scaled_cells = scaled.submobjects
        weights_title, _, _, weight_cells = weights.submobjects
        output = VGroup(*[text("출력 토큰 " + str(i+1) + "  →  " + ", ".join(f"{v:.2f}" for v in row), 21, P.result)
                          for i, row in enumerate(p["output"])])
        output.arrange(DOWN, buff=.3).move_to([0, .55, 0])
        value_rows = VGroup(*[text(f"V{i+1} = [" + ", ".join(f"{v:.2f}" for v in row) + "]", 16, P.sensor)
                              for i, row in enumerate(p["v"])])
        value_rows.arrange(DOWN, buff=.12).move_to([0, -1.3, 0])
        note = text("각 출력 = 해당 행의 가중치 × V", 20, P.active).move_to([0, 1.75, 0])
        def reveal(group):
            title, rows, cols, cells = group.submobjects
            return AnimationGroup(FadeIn(title), FadeIn(rows), FadeIn(cols),
                                  LaggedStart(*[FadeIn(cell, shift=UP*.08) for cell in cells], lag_ratio=.08),
                                  lag_ratio=.05).set_run_time(2.2)
        def matrix_update(cells, next_cells, old_title, next_title):
            move_cells = Transform(cells, next_cells).set_run_time(.65)
            change_title = AnimationGroup(FadeOut(old_title), FadeIn(next_title)).set_run_time(.65)
            return AnimationGroup(move_cells, change_title, lag_ratio=0).set_run_time(.65)
        return VGroup(raw, scaled, weights, output, note), [
            [reveal(raw)], [matrix_update(score_cells, scaled_cells, raw_title, scaled_title)],
            [matrix_update(score_cells, weight_cells, scaled_title, weights_title)],
            [FadeOut(score_cells), FadeOut(row_tags), FadeOut(col_tags), FadeOut(weights_title),
             FadeIn(note), FadeIn(output), FadeIn(value_rows)]]
