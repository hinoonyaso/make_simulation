"""Small data-driven Manim renderer for the current executable mechanism pilots."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, P
from core.mechanism.storyboard import validate_phase_contract
from core.mechanism.timeline import validate_timeline
from core.mechanism.pid_playback import PIDPlayback


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
        timeline = json.loads(Path(os.environ["V11_TIMELINE_PATH"]).read_text(encoding="utf-8"))
        errors = validate_timeline(timeline, expected_phase_ids=[beat.get("phase_id") for beat in beats])
        if errors:
            raise ValueError("invalid shared mechanism timeline: " + "; ".join(errors))
        fps = timeline["fps"]
        if fps != 30:
            raise ValueError("common Manim renderer requires a 30 fps shared timeline")
        phases = {phase["phase_id"]: phase for phase in timeline["phases"]}
        self.add(text(self.plan["title"], 34, P.fg, 13.2).to_edge(UP, buff=.35))
        if self.plan["kind"] == "mcu_pid":
            self._render_pid(timeline)
            return
        graphic, transitions = self._build_graphic()
        errors = validate_phase_contract(beats, transitions)
        if errors:
            raise ValueError("invalid storyboard/renderer phase contract: " + "; ".join(errors))
        for index, beat in enumerate(beats):
            phase = phases[beat["phase_id"]]
            duration_frames = phase["presentation_end_frame"] - phase["presentation_start_frame"]
            duration = duration_frames / fps
            caption = text(beat["caption"], 20, P.muted, 12.5).move_to([0, -3.1, 0])
            header = text(f"{index+1:02d} / {len(beats):02d}", 16, P.active).to_corner(UR, buff=.4)
            anims = [FadeIn(header), FadeIn(caption)]
            state_animations = transitions[beat["phase_id"]]
            anims.extend(state_animations)
            state_runtime = max([value for animation in state_animations
                                 if isinstance((value := getattr(animation, "run_time", .6)), (int, float))] + [.6])
            minimum_frames = max(1, int(round(state_runtime * fps)))
            if minimum_frames > duration_frames:
                raise ValueError(f"phase {beat['phase_id']} needs {minimum_frames} transition frames, "
                                 f"only {duration_frames} presentation frames are available")
            self.play(*anims, run_time=minimum_frames / fps)
            self.wait((duration_frames - minimum_frames) / fps)
            self.remove(header, caption)

    def _build_graphic(self):
        kind = self.plan["kind"]
        if kind == "quantization":
            graphic, rows = self._quantization()
            keys = ["input", "integer_mapping", "dequantization"]
            if self.plan.get("activation_quantization"):
                keys.append("activation_quantization")
            return graphic, dict(zip(keys, rows))
        if kind == "nms": return self._nms()
        if kind == "mujoco_arm":
            graphic, rows = self._mujoco_arm()
            return graphic, dict(zip(["robot_setup", "joint_state", "end_effector_motion"], rows))
        if kind == "self_attention":
            graphic, rows = self._self_attention()
            return graphic, dict(zip(["input_projection", "qk_scores", "scaling_mask", "softmax", "weighted_value"], rows))
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
        code_labels = VGroup(*[text(f"{int(value)}", 12, P.active).next_to(mob, DOWN, buff=.06)
                               for value, mob in zip(quantized, quant_dots)])
        activation_group = VGroup()
        activation = p.get("activation_quantization")
        if activation:
            activation_values = list(zip(flat_values(activation["original"]),
                                         flat_values(activation["quantized"]),
                                         flat_values(activation["dequantized"])))[:7]
            rows = [text(f"활성값 {i+1}: {x:.3f} → {int(q)} → {restored:.3f}", 17, P.sensor, 8.8)
                    for i, (x, q, restored) in enumerate(activation_values)]
            activation_group = VGroup(text("별도 보정 범위로 활성값을 변환", 20, P.sensor), *rows,
                text(f"weight 최대 오차={p['max_absolute_error']:.5g}", 16, P.result),
                text(f"activation scale={np.asarray(activation['scale']).reshape(-1)[0]:.5g} · "
                     f"zero point={np.asarray(activation['zero_point']).reshape(-1)[0]:g} · "
                     f"최대 오차={activation['max_absolute_error']:.5g}", 16, P.sensor, 11))
            activation_group.arrange(DOWN, buff=.17).move_to([0, 0, 0])
        graphic = VGroup(axis, axis_labels, original_dots, quant_dots, restored_dots, value_labels,
                         scale_label, error_label, code_labels)
        if activation:
            graphic.add(activation_group)
        return graphic, [[Create(axis), FadeIn(axis_labels), FadeIn(original_dots), FadeIn(value_labels)],
                         [FadeIn(quant_dots), FadeIn(code_labels), FadeIn(scale_label)],
                         [FadeIn(restored_dots), FadeIn(error_label)]] + ([[
                             FadeOut(axis), FadeOut(axis_labels), FadeOut(original_dots), FadeOut(quant_dots),
                             FadeOut(restored_dots), FadeOut(value_labels), FadeOut(code_labels),
                             FadeOut(scale_label), FadeOut(error_label), FadeIn(activation_group)] ] if activation else [])

    def _nms(self):
        p = self.plan
        boxes = np.asarray(p["boxes_xyxy"], dtype=float)
        if not len(boxes):
            canvas = Rectangle(width=7.8, height=4.0, color=P.faint).move_to([-2.3, -.1, 0])
            threshold = text(f"confidence ≥ {p['confidence_threshold']:.2f}    IoU threshold = {p['iou_threshold']:.2f}",
                             20, P.muted).move_to([2.7, 2.3, 0])
            empty = text("비교할 검출 후보가 없습니다.", 23, P.active, 6.5).move_to([-2.3, 0, 0])
            result = text("유지 상자: 없음", 20, P.result).move_to([2.7, -2.45, 0])
            return VGroup(canvas, threshold, empty, result), {
                "candidates": [Create(canvas), FadeIn(threshold), FadeIn(empty)],
                "final_result": [FadeIn(result)]}
        lo, hi = boxes[:, :2].min(axis=0), boxes[:, 2:].max(axis=0)
        span = np.maximum(hi - lo, 1.0)
        canvas = Rectangle(width=7.8, height=4.0, color=P.faint).move_to([-2.3, -.1, 0])
        palette = [P.sensor, P.active, P.result, P.error, P.muted]
        candidates = VGroup()
        candidate_groups = {}
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
            candidate = VGroup(rect, label)
            candidates.add(candidate); candidate_groups[item_id] = candidate; box_mobs[item_id] = rect
            labels.add(label)
        threshold = text(f"confidence ≥ {p['confidence_threshold']:.2f}    IoU threshold = {p['iou_threshold']:.2f}",
                         20, P.muted).move_to([2.7, 2.3, 0])
        kept_label = (f"최종 유지: {len(p['kept_ids'])}개" if not p["kept_ids"] else
                      f"최종 유지: {len(p['kept_ids'])}개 · " + ", ".join(p["kept_ids"]))
        result = text(kept_label, 18, P.result, 6.2).move_to([2.7, -2.45, 0])
        comparison_label = text("confidence 통과 후보를 점수 순서로 비교", 17, P.active, 5.0).move_to([3.55, .3, 0])
        graphic = VGroup(canvas, candidates, threshold, result, comparison_label)
        steps = p["steps"]
        confidence_pass = set(p["confidence_pass_ids"])
        filtered = [FadeOut(group) for item_id, group in candidate_groups.items() if item_id not in confidence_pass]
        filter_label = text(f"confidence 통과 {len(confidence_pass)} / {len(p['ids'])}개",
                            20, P.active).move_to([2.7, 1.35, 0])
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
        transitions = {"candidates": [Create(canvas), FadeIn(threshold), FadeIn(candidates)],
                       "confidence_filter": [*filtered, FadeIn(filter_label)],
                       "final_result": [*[mob.animate.set_stroke(color=P.result if item in p["kept_ids"] else P.muted)
                                           for item, mob in box_mobs.items()], FadeIn(result)]}
        if steps:
            transitions["iou_comparison"] = [comparison_sequence]
        return graphic, transitions

    def _render_pid(self, timeline):
        playback = PIDPlayback(self.plan, timeline)
        rows, p = self.plan['samples'], self.plan
        x0, x1, y0 = -5.8, 1.8, -1.3
        max_t = max(row['time_s'] for row in rows) or 1.
        scale = max(1., max(abs(row[k]) for row in rows
                           for k in ('target_rad_s', 'motor_speed_rad_s', 'encoder_speed_rad_s')))
        def x(t): return x0 + (x1-x0)*t/max_t
        def y(v): return y0 + 2.8*v/scale
        self.add(Line([x0,y0,0],[x1,y0,0],color=P.faint),
                 text("목표 / 모터 / 엔코더 · rad/s",18,P.muted).move_to([-2,2.6,0]),
                 text("PWM [-1, 1] · 기록된 표본 유지",17,P.muted).move_to([-2,-2.5,0]))
        def curve(key, color, discrete=False, pwm=False):
            points=[]
            previous=None
            for row in rows:
                value = row[key]
                yy = (-2+value*.35) if pwm else y(value)
                if discrete and previous is not None:
                    points.append([x(row['time_s']), previous, 0])
                points.append([x(row['time_s']), yy, 0]); previous=yy
            return polyline(points,color,2)
        self.add(curve('target_rad_s',P.active,True),curve('motor_speed_rad_s',P.result),
                 curve('encoder_speed_rad_s',P.sensor,True),curve('pwm_duty',P.active,True,True))
        cursor=Line([x0,y0-.1,0],[x0,2.1,0],color=P.active)
        encoder_dot=Dot(radius=.065,color=P.sensor)
        motor_dot=Dot(radius=.065,color=P.result)
        pwm_dot=Dot(radius=.065,color=P.active)
        panel=VGroup(); footer=VGroup()
        self.add(cursor,encoder_dot,motor_dot,pwm_dot,panel,footer)
        observed={}
        debug_path=os.environ.get('V115_FRAME_DEBUG')
        last_key=None
        def display(frame):
            nonlocal last_key
            state=playback.state(frame)
            source=state['source_time_sec']; sample=state['sample_time_sec']
            cursor.set_x(x(source))
            encoder_dot.move_to([x(sample),y(state['encoder_speed_rad_s']),0])
            motor_dot.move_to([x(sample),y(state['motor_speed_rad_s']),0])
            pwm_dot.move_to([x(sample),-2+state['pwm_duty']*.35,0])
            key=(state['phase_id'],state['sample_index'])
            if key != last_key:
                lines=[f"표본 {state['sample_index']} · t={sample:.2f}s",
                       f"목표 {state['target_rad_s']:.2f} · 오차 {state['error_rad_s']:.2f}",
                       f"P {state['p_term']:.3f}   I {state['i_term']:.3f}   D {state['d_term']:.3f}",
                       f"PWM {state['pwm_duty']:.3f}",
                       f"모터 {state['motor_speed_rad_s']:.2f} rad/s",
                       f"엔코더 {state['encoder_speed_rad_s']:.2f} rad/s",
                       f"누적 계수 {state['encoder_count']}"]
                panel.become(VGroup(*[text(v,18,P.fg,4.5) for v in lines]).arrange(DOWN,buff=.23,aligned_edge=LEFT).move_to([4.3,.2,0]))
                last_key=key
            footer.become(text(f"영상 프레임 {frame} · 원본 t={source:.3f}s · {state['playback_state']}",16,P.muted).move_to([0,-3.25,0]))
            if debug_path: observed[frame]=state
        for phase in timeline['phases']:
            start,end=phase['presentation_start_frame'],phase['presentation_end_frame']
            display(start)
            # Manim renders alpha=i/N, with finish(alpha=1) after the last frame.
            def update(_,alpha,start=start,end=end):
                display(min(end-1,start+int(round(alpha*(end-start)))))
            self.play(UpdateFromAlphaFunc(cursor,update,rate_func=linear),run_time=(end-start)/timeline['fps'])
        if debug_path:
            Path(debug_path).write_text(json.dumps([observed[i] for i in sorted(observed)],ensure_ascii=False),encoding='utf-8')

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
        projected_rows = []
        for index, token in enumerate(p["tokens"]):
            vector_text = lambda values: "[" + ", ".join(f"{float(v):.2f}" for v in values) + "]"
            projected_rows.append(text(f"토큰 {index+1}  {vector_text(token)}   →   "
                f"Q {vector_text(p['q'][index])}   K {vector_text(p['k'][index])}   V {vector_text(p['v'][index])}",
                17, P.fg, 12.2))
        projection = VGroup(text("입력 벡터를 세 경로로 투영", 24, P.active), *projected_rows)
        projection.arrange(DOWN, buff=.32).move_to([0, .1, 0])
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
        has_mask = any(any(bool(value) for value in row) for row in p.get("causal_mask", []))
        scaled_title_text = f"차원으로 나눈 점수 · ÷ {p['scale_factor']:.2f}"
        if has_mask:
            scaled_title_text += " · 미래 위치 가림"
        scaled = matrix(p["scaled_scores"], scaled_title_text, P.sensor)
        weights = matrix(p["attention_weights"], "행마다 정규화한 softmax 가중치", P.result)
        raw_title, row_tags, col_tags, score_cells = raw.submobjects
        scaled_title, _, _, scaled_cells = scaled.submobjects
        weights_title, _, _, weight_cells = weights.submobjects
        mask_marks = VGroup()
        if has_mask:
            for row in range(n):
                for col in range(n):
                    if p["causal_mask"][row][col]:
                        mask_marks.add(Cross(scaled_cells[row*n+col], stroke_color=P.error, stroke_width=3))
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
        return VGroup(projection, raw, scaled, weights, output, note), [
            [FadeIn(projection)],
            [FadeOut(projection), reveal(raw)],
            [matrix_update(score_cells, scaled_cells, raw_title, scaled_title),
             *([FadeIn(mask_marks)] if has_mask else [])],
            [*([FadeOut(mask_marks)] if has_mask else []),
             matrix_update(score_cells, weight_cells, scaled_title, weights_title)],
            [FadeOut(score_cells), FadeOut(row_tags), FadeOut(col_tags), FadeOut(weights_title),
             FadeIn(note), FadeIn(output), FadeIn(value_rows)]]
