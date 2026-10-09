"""Render a short visualization of one real YOLO11 image inference trace.

This is an image-space detector trace. It does not infer depth or simulate a robot.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from manim import *

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core/manim-robotics-education-skill/templates"))
from manim_kit import apply_theme, txt, P
sys.path.insert(0, str(ROOT))
from core.mechanism.timeline import validate_timeline

# Resolution and frame rate are selected by the common renderer's CLI flags.


class YoloInferenceScene(Scene):
    def construct(self):
        apply_theme(self)
        trace_path = Path(os.environ["YOLO_TRACE_PATH"])
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        manifest = json.loads(Path(os.environ["YOLO_MANIFEST_PATH"]).read_text(encoding="utf-8"))
        timeline_path = Path(os.environ["YOLO_TIMELINE_PATH"])
        timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        phase_ids = [beat.get("phase_id") for beat in manifest.get("beats", [])]
        expected_phases = ["candidates", "confidence_filter", "iou_comparison", "final_result"]
        if phase_ids != expected_phases:
            raise ValueError(f"YOLO scene requires manifest phases {expected_phases}; received {phase_ids}")
        errors = validate_timeline(timeline, expected_phase_ids=expected_phases)
        if errors:
            raise ValueError("invalid YOLO mechanism timeline: " + "; ".join(errors))
        if timeline["fps"] != 30:
            raise ValueError("YOLO Manim renderer requires a 30 fps shared timeline")
        fps = timeline["fps"]
        phases = {phase["phase_id"]: phase for phase in timeline["phases"]}
        designed_seconds = {"candidates": 2.75, "confidence_filter": 2.3,
                            "iou_comparison": 4.35, "final_result": 1.75}

        def begin_phase(phase_id):
            phase = phases[phase_id]
            start_frame = int(round(self.renderer.time * fps))
            expected = phase["presentation_start_frame"]
            if start_frame != expected:
                raise RuntimeError(f"YOLO phase {phase_id} starts at frame {start_frame}; expected {expected}")
            allotted = phase["presentation_end_frame"] - expected
            scale = min(1.0, allotted / (designed_seconds[phase_id] * fps))
            self._phase_schedule = {"scale": scale, "fps": fps, "seconds": 0.0,
                                    "frames": 0, "phase_id": phase_id}
            return start_frame

        def phase_play(*animations, run_time=1.0):
            schedule = self._phase_schedule
            end_frames = round((schedule["seconds"] + run_time) * schedule["scale"] * schedule["fps"])
            frames = max(1, end_frames - schedule["frames"])
            schedule["seconds"] += run_time
            schedule["frames"] += frames
            self.play(*animations, run_time=frames / schedule["fps"])

        def phase_wait(seconds):
            schedule = self._phase_schedule
            end_frames = round((schedule["seconds"] + seconds) * schedule["scale"] * schedule["fps"])
            frames = max(1, end_frames - schedule["frames"])
            schedule["seconds"] += seconds
            schedule["frames"] += frames
            self.wait(frames / schedule["fps"])

        def finish_phase(phase_id, start_frame):
            phase = phases[phase_id]
            elapsed = int(round(self.renderer.time * fps)) - start_frame
            allotted = phase["presentation_end_frame"] - start_frame
            if elapsed > allotted:
                raise RuntimeError(f"YOLO phase {phase_id} used {elapsed} frames; timeline allows {allotted}")
            remaining = allotted - elapsed
            if remaining:
                self.wait(remaining / fps)
            actual_end = int(round(self.renderer.time * fps))
            if actual_end != phase["presentation_end_frame"]:
                raise RuntimeError(f"YOLO phase {phase_id} ended at frame {actual_end}; "
                                   f"expected {phase['presentation_end_frame']}")
        image_path = Path(trace["input_image"]["path"])
        image = ImageMobject(str(image_path)).scale_to_fit_height(5.15).move_to([-3.65, -.05, 0])
        image_frame = RoundedRectangle(width=image.width + .12, height=image.height + .12,
                                       corner_radius=.08, color=P.faint).move_to(image)
        title = txt("YOLO는 이미지에서 어떻게 후보를 고를까?", 35, P.fg).to_edge(UP, buff=.28)
        footer = txt("실제 YOLO11n 추론 결과 · 이미지 좌표 · CPU", 18, P.muted).to_edge(DOWN, buff=.18)
        self.add(title, image_frame, image, footer)

        phase_start = begin_phase("candidates")

        panel_x = 2.55
        label = txt("입력 이미지", 24, P.sensor).move_to([panel_x, 2.12, 0])
        count = txt(f"모델 출력 {trace['raw_prediction_count']:,}개", 26, P.fg).move_to([panel_x, 1.15, 0])
        threshold = txt(f"신뢰도 기준 {trace['thresholds']['confidence']:.2f}", 23, P.active).move_to([panel_x, .35, 0])
        passed = txt(f"통과 {trace['confidence_pass_count']}개", 26, P.result).move_to([panel_x, -.55, 0])
        rejected = txt(f"제외 {trace['confidence_reject_count_above_display_floor']}개", 24, P.error).move_to([panel_x, -1.32, 0])
        note = txt("표시는 추적용 후보 일부\n계산은 전체 후보로 수행", 18, P.muted).move_to([panel_x, -2.35, 0])
        phase_play(FadeIn(label), run_time=.5)
        phase_play(FadeIn(count), run_time=.7)
        phase_wait(.5)

        candidate_by_id = {item["id"]: item for item in trace["candidates"]}
        image_w, image_h = trace["input_image"]["width"], trace["input_image"]["height"]
        scale = image.height / image_h

        def box_for(item, color, stroke=3.2):
            x1, y1, x2, y2 = item["xyxy"]
            width, height = max(.03, (x2 - x1) * scale), max(.03, (y2 - y1) * scale)
            cx = image.get_left()[0] + (x1 + x2) * .5 * scale
            cy = image.get_top()[1] - (y1 + y2) * .5 * scale
            return Rectangle(width=width, height=height, color=color, stroke_width=stroke).move_to([cx, cy, 0])

        visible = [candidate_by_id[item_id] for item_id in trace["visualization_candidate_ids"]]
        rejected_item = next((item for item in visible if item["score"] < trace["thresholds"]["confidence"]), None)
        candidate_count = txt(f"추적 후보 {trace['trace_candidate_count']}개 (≥0.05)", 23, P.fg).move_to(count)
        phase_play(Transform(count, candidate_count), run_time=.55)
        finish_phase("candidates", phase_start)

        phase_start = begin_phase("confidence_filter")
        if rejected_item:
            reject_box = box_for(rejected_item, P.error)
            rejection_text = txt(f"기준 0.25 · 후보 {rejected_item['score']:.2f} 탈락", 19, P.error)
            rejection_text.move_to(threshold)
            phase_play(FadeIn(threshold), FadeIn(rejected), run_time=.5)
            phase_play(Create(reject_box), Transform(threshold, rejection_text), run_time=.7)
            phase_wait(.65)
            phase_play(Uncreate(reject_box), threshold.animate.set_opacity(.25), run_time=.45)
        else:
            phase_play(FadeIn(threshold), FadeIn(rejected), run_time=.6)

        finish_phase("confidence_filter", phase_start)

        phase_start = begin_phase("iou_comparison")

        stage_nms = txt("겹침 비교 · IoU NMS", 22, P.active).move_to(label)
        passed_count = txt(f"신뢰도 통과 {trace['confidence_pass_count']}개", 25, P.fg).move_to(count)
        phase_play(Transform(label, stage_nms), Transform(count, passed_count),
                  FadeOut(VGroup(threshold, passed, rejected, note)), run_time=.65)
        self.remove(threshold, passed, rejected, note)
        transient_nms = []
        first_suppression = next(((step["winner_id"], comp)
                                  for step in trace["nms_steps"]
                                  for comp in step["comparisons"] if comp["suppressed"]), None)
        if first_suppression:
            winner_id, suppression = first_suppression
            winner = candidate_by_id[winner_id]
            loser = candidate_by_id[suppression["candidate_id"]]
            winner_box = box_for(winner, P.result, 4)
            loser_box = box_for(loser, P.error, 4)
            winner_tag = txt(f"유지 {winner['class_name']} {winner['score']:.2f}", 17, P.result)
            loser_tag = txt(f"겹침 IoU {suppression['iou']:.2f} > {trace['thresholds']['iou']:.2f}", 17, P.error)
            transient_nms.extend([winner_tag, loser_tag])
            winner_tag.move_to([panel_x, .15, 0]); loser_tag.move_to([panel_x, -.35, 0])
            phase_play(Create(winner_box), Create(loser_box), FadeIn(winner_tag), FadeIn(loser_tag), run_time=1.0)
            phase_wait(.9)
            explanation = txt("같은 종류의 겹친 후보는\n점수가 낮으면 제거", 22, P.fg).move_to([panel_x, -1.35, 0])
            transient_nms.append(explanation)
            phase_play(FadeIn(explanation), Uncreate(loser_box), loser_tag.animate.set_opacity(.25), run_time=.7)
            phase_wait(.7)
            phase_play(Uncreate(winner_box), winner_tag.animate.set_opacity(.25),
                      explanation.animate.set_opacity(.25), run_time=.4)
            self.remove(winner_box, loser_box, winner_tag, loser_tag, explanation)
        if transient_nms:
            self.remove(*transient_nms)

        finish_phase("iou_comparison", phase_start)

        phase_start = begin_phase("final_result")

        final_boxes = VGroup()
        final_labels = VGroup()
        for index, detection in enumerate(trace["model_final_detections"], start=1):
            item = candidate_by_id[detection["id"]]
            rect = box_for(item, P.result, 4)
            final_boxes.add(rect)
            x1, y1, x2, _ = item["xyxy"]
            badge_x = image.get_left()[0] + (x1 + min(18, (x2-x1)*.35)) * scale
            badge_y = image.get_top()[1] - (y1 + 18) * scale
            badge = Circle(radius=.12, stroke_width=1, color=P.result,
                           fill_color=P.result, fill_opacity=1).move_to(
                               [max(image.get_left()[0] + .13, badge_x),
                                min(image.get_top()[1] - .13, badge_y), 0])
            number = txt(str(index), 12, P.bg).move_to(badge)
            final_labels.add(VGroup(badge, number))
        result_title = txt(f"최종 검출 {len(final_boxes)}개", 28, P.result).move_to([panel_x, 1.15, 0])
        details = [txt(f"{i}. {candidate_by_id[item['id']]['class_name']}  {item['score']:.2f}", 20, P.fg)
                   for i, item in enumerate(trace["model_final_detections"], start=1)]
        result_detail = VGroup(*details).arrange(DOWN, aligned_edge=LEFT, buff=.22).move_to([panel_x, -.75, 0])
        stage_result = txt("최종 검출", 23, P.result).move_to(label)
        phase_play(Create(final_boxes), FadeIn(final_labels), Transform(count, result_title),
                  Transform(label, stage_result), run_time=1.25)
        phase_play(FadeIn(result_detail), run_time=.5)
        finish_phase("final_result", phase_start)
        final_frame = int(round(self.renderer.time * fps))
        if final_frame != timeline["total_frames"]:
            raise RuntimeError(f"YOLO output ended at frame {final_frame}; timeline requires {timeline['total_frames']}")
