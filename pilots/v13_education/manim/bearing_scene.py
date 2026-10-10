"""Manim support visualization for two bearing concept beats."""
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


class BearingLessonScene(Scene):
    def construct(self):
        manifest = json.loads(Path(os.environ["V13_MANIFEST_PATH"]).read_text(encoding="utf-8"))
        timeline = json.loads(Path(os.environ["V13_TIMELINE_PATH"]).read_text(encoding="utf-8"))
        by_id = {phase["phase_id"]: phase for phase in timeline["phases"]}
        apply_theme(self)
        for beat in manifest["beats"]:
            phase = by_id[beat["phase_id"]]
            duration = (phase["presentation_end_frame"]-phase["presentation_start_frame"])/timeline["fps"]
            if beat.get("tool") != "M":
                self.wait(duration)
                continue
            self._render_beat(beat, duration)

    def _render_beat(self, beat, duration):
        total_frames = round(duration * 30)
        title = txt(beat.get("visual_caption", beat["caption"]), 29, P.fg).to_edge(UP, buff=.4)
        left_title = txt("미끄럼", 24, P.muted).move_to([-3.1, 1.55, 0])
        right_title = txt("구름", 24, P.active).move_to([3.1, 1.55, 0])
        left_surface = Line([-5.2,-1.35,0],[-1,-1.35,0],color=P.faint,stroke_width=5)
        right_surface = Line([1,-1.35,0],[5.2,-1.35,0],color=P.faint,stroke_width=5)
        if beat["phase_id"] == "contact_compare":
            block = RoundedRectangle(width=1.05,height=.65,corner_radius=.08,
                                     fill_color=P.sensor,fill_opacity=1,stroke_color=P.sensor)
            block.move_to([-3.1,-.94,0])
            ball = Circle(radius=.36,color=P.result,fill_color=P.result,fill_opacity=1).move_to([2.0,-.98,0])
            bearing = Circle(radius=.12,color=P.fg,fill_color=P.fg,fill_opacity=1).move_to([2.0,-.98,0])
            spin_mark = Dot([2.27,-.98,0],radius=.055,color=YELLOW)
            motion_left = Arrow([-3.8,-.2,0],[-1.5,-.2,0],buff=0,color=P.error,stroke_width=5)
            motion_right = Arrow([1.2,-.2,0],[3.8,-.2,0],buff=0,color=P.active,stroke_width=5)
            groups = VGroup(title,left_title,right_title,left_surface,right_surface,block,ball,bearing,spin_mark,
                            motion_left,motion_right)
            intro_frames = min(33, round(total_frames*.22))
            outro_frames = min(8, round(total_frames*.10))
            remain_frames = max(1,total_frames-intro_frames-outro_frames)
            self.play(*[FadeIn(item) for item in groups],run_time=intro_frames/30)
            driver = ValueTracker(0)
            def update_rolling(_mob, alpha):
                center = [2.0 + 1.15*alpha, -.98, 0]
                ball.move_to(center)
                bearing.move_to(center)
                angle = -TAU*alpha
                spin_mark.move_to([center[0]+.27*np.cos(angle), center[1]+.27*np.sin(angle), 0])
            self.play(block.animate.shift(RIGHT*1.15),
                      UpdateFromAlphaFunc(driver, update_rolling, rate_func=linear),
                      run_time=remain_frames/30, rate_func=linear)
            self.play(*[FadeOut(item) for item in groups],run_time=outro_frames/30)
        else:
            labels = VGroup(title, txt("구름 접촉도 실제 부품에서는",20,P.fg).move_to([0,.65,0]),
                txt("탄성 변형",24,P.active).move_to([-3.4,-.1,0]),
                txt("윤활",24,P.active).move_to([0,-.1,0]),
                txt("미세 미끄럼",24,P.active).move_to([3.4,-.1,0]),
                txt("마찰과 발열을 완전히 없애지는 않습니다",20,P.muted).move_to([0,-1.2,0]),
                )
            intro_frames = min(30, round(total_frames*.2))
            outro_frames = min(9, round(total_frames*.1))
            remain_frames = max(1,total_frames-intro_frames-outro_frames)
            self.play(*[FadeIn(item) for item in labels],run_time=intro_frames/30)
            self.wait(remain_frames/30)
            self.play(*[FadeOut(item) for item in labels],run_time=outro_frames/30)
