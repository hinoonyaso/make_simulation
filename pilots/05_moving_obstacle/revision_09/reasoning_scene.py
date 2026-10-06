"""One run: map update -> replanned reference -> feedback-driven physical position."""
import json, sys, math
from pathlib import Path
import numpy as np
from manim import *
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parents[2] / 'core/manim-robotics-education-skill/templates'))
from manim_kit import P, BeatClock, beat_seconds, txt, apply_theme
DOC = json.loads((H / 'visual_manifest.json').read_text())
D = json.loads((H / DOC['beats'][3]['trace']).read_text())
ROWS = D['samples']
INITIAL = D['plans'][0]['path']
NEW = D['plans'][1]['path']
RADIUS = D['config']['drum_radius_m'] + D['planner_config']['robot_radius_m'] + D['planner_config']['margin_m']

def W(x, y):
    return np.array([x * 2.8, y * 2.8 - 0.2, 0.0])

def label(s, size=31, color=P.fg):
    return txt(s, size=size, color=color)

def path(points, color, width=5):
    return VMobject(stroke_color=color, stroke_width=width, fill_opacity=0).set_points_as_corners([W(*p) for p in points])

def robot(row):
    r = Rectangle(width=0.26 * 2.8, height=0.22 * 2.8, fill_color='#394455', fill_opacity=1, stroke_color=P.fg).shift([-0.064 * 2.8, 0, 0])
    wh = VGroup(*[RoundedRectangle(width=0.16, height=0.1, corner_radius=0.025, fill_opacity=1, color=P.fg).shift([0, s * 0.144 * 2.8, 0]) for s in [-1, 1]])
    return VGroup(r, wh).rotate(row['yaw_rad']).shift(W(*row['root_position_m'][:2]))

def change_sentence(old, new):
    """Local text replacement; geometry remains visible and callers retain new."""
    return Succession(FadeOut(old), FadeIn(new))

class ClosedLoopReasoning(Scene):

    def construct(self):
        apply_theme(self)
        dur = beat_seconds(H / 'visual_manifest.json', 'B02', 'B03', 'B04')
        heading = label('실물과 지도 정보는 다릅니다', 39).move_to([0, 3.35, 0])
        grid = VGroup(*[Line(W(x, -1.0), W(x, 1.0), stroke_color=P.faint, stroke_width=0.5, stroke_opacity=0.3) for x in np.arange(-1.8, 1.81, 0.1)], *[Line(W(-1.8, y), W(1.8, y), stroke_color=P.faint, stroke_width=0.5, stroke_opacity=0.3) for y in np.arange(-1.0, 1.01, 0.1)])
        drum = Circle(radius=0.3 * 2.8, color='#D98150', fill_color='#D98150', fill_opacity=0.35).move_to(W(0, 0))
        old = path(INITIAL, P.muted)
        bot = robot(ROWS[0])
        goal = Circle(radius=0.15 * 2.8, color=P.result, stroke_width=3).move_to(W(1.3, 0))
        goal_label = label('목표', 25, P.result).next_to(goal, RIGHT, buff=0.15)
        known = label('지도 정보 없음 · 드럼은 실제로 존재', 25, P.muted).move_to([0, 2.65, 0])
        self.add(grid, drum, old, bot, goal, goal_label, heading, known)
        forbidden = Circle(radius=RADIUS * 2.8, stroke_color=P.error, stroke_width=3, fill_color=P.error, fill_opacity=0.09).move_to(W(0, 0))
        radius_label = label('금지 반경\n0.77m', 28, P.error).move_to([4.25, 1.3, 0])
        with BeatClock(self, dur[0]) as b:
            b.wait(4.1)
            known_next = label('지도 정보 추가 · 실험 2초', 27, P.fg).move_to([0, 2.65, 0])
            b.play(change_sentence(known, known_next), Transform(bot, robot(ROWS[60])), drum.animate.set_fill(opacity=0.75), run_time=0.6)
            known = known_next
            b.wait(0.8)
            b.play(GrowFromCenter(forbidden), FadeIn(radius_label), run_time=1.5)
        invalid = [p for p in INITIAL if math.hypot(*p) < RADIUS]
        invalid_line = path(invalid, P.error, 8)
        new = path(NEW, P.result, 5)
        with BeatClock(self, dur[1]) as b:
            heading_next = label('이전 길을 그대로 쓸 수 있을까?', 38).move_to([0, 3.35, 0])
            b.play(change_sentence(heading, heading_next), FadeOut(known), FadeIn(invalid_line), run_time=0.6)
            heading = heading_next
            b.wait(3.5)
            b.play(old.animate.set_opacity(0.35), Create(new), run_time=2.9)
            b.wait(1.7)
            heading_next = label('새 경로는 물리 위치 명령이 아닙니다', 37).move_to([0, 3.35, 0])
            b.play(change_sentence(heading, heading_next), Indicate(bot, color=P.sensor, scale_factor=1.15), run_time=1.0)
            heading = heading_next
        clock = ValueTracker(2)
        row = ROWS[60]
        prev = ROWS[59]
        origin = W(*prev['root_position_m'][:2])
        target = W(*row['lookahead_m'])
        yaw = prev['yaw_rad']
        desired = math.atan2(target[1] - origin[1], target[0] - origin[0])
        i = min(range(len(NEW)), key=lambda k: math.dist(prev['root_position_m'][:2], NEW[k]))
        j = i
        length = 0
        while j < len(NEW) - 1 and length < 0.3:
            length += math.dist(NEW[j], NEW[j + 1])
            j += 1
        assert math.dist(NEW[j], row['lookahead_m']) < 1e-06
        selected = path(NEW[i:j + 1], P.result, 9)
        point = Dot(target, radius=0.09, color=P.result)
        point_label = label('조금 앞의 목표점', 26, P.result).move_to([-4.0, 1.9, 0])
        actual_arrow = Arrow(origin, origin + np.array([math.cos(yaw), math.sin(yaw), 0]) * 1.5, buff=0, color=P.sensor, stroke_width=5)
        target_arrow = Arrow(origin, origin + np.array([math.cos(desired), math.sin(desired), 0]) * 1.8, buff=0, color=P.result, stroke_width=5)
        error_arc = Arc(radius=0.9, start_angle=yaw, angle=desired - yaw, color=P.fg, stroke_width=4).shift(origin)
        current_label = label('지금 보는 방향', 25, P.sensor).move_to([-4.1, -1.05, 0])
        target_label = label('목표점 쪽 · 왼쪽', 25, P.result).move_to([-4.1, 0.95, 0])
        note = label('앞의 지점을 향해 방향을 맞춥니다', 30).move_to([0, 2.6, 0])
        actual = always_redraw(lambda: path([r['root_position_m'][:2] for r in ROWS[:max(2, min(901, round(clock.get_value() * 30) + 1))]], P.sensor, 5))
        flow = VGroup(*[label(s, 25, P.sensor if i == 0 else P.muted) for i, s in enumerate(['실제 위치', '→ 바퀴 명령', '→ 물리 반응', '→ 다시 위치'])]).arrange(RIGHT, buff=0.25).move_to([0, -2.75, 0])
        cues = json.loads((H / 'output/caption_timing.json').read_text())
        audio = json.loads((H / 'assets/audio/manifest.json').read_text())
        start = next((r['start'] for r in audio if r['beat'] == 'B04'))
        anchors = [c['start'] - start for c in cues if c.get('beat') == 'B04' or start <= c['start'] < start + dur[2]]
        assert len(anchors) == 5, anchors
        with BeatClock(self, dur[2]) as b:
            heading_next = label('왜 왼쪽으로 돌라는 명령이 나올까?', 37).move_to([0, 3.35, 0])
            b.play(change_sentence(heading, heading_next), FadeOut(radius_label), FadeOut(invalid_line), old.animate.set_opacity(0.15), Transform(bot, robot(prev)), Create(selected), FadeIn(point), FadeIn(point_label), FadeIn(note), run_time=0.8)
            heading = heading_next
            b.wait(max(0, anchors[1] - 0.8))
            b.play(GrowArrow(actual_arrow), FadeIn(current_label), run_time=0.6)
            b.play(GrowArrow(target_arrow), Create(error_arc), FadeIn(target_label), run_time=0.7)
            b.wait(max(0, anchors[2] - anchors[1] - 1.3))
            note_next = label('목표점이 왼쪽 → 왼쪽으로 보정', 30).move_to([0, 2.6, 0])
            b.play(change_sentence(note, note_next), run_time=0.5)
            note = note_next
            b.play(Indicate(error_arc, scale_factor=1.15), run_time=0.6)
            b.wait(max(0, anchors[3] - anchors[2] - 1.1))
            aligned = Arrow(origin, origin + np.array([math.cos(desired), math.sin(desired), 0]) * 1.5, buff=0, color=P.sensor, stroke_width=5)
            current_label_next = label('가정: 현재 방향만 정렬', 25, P.sensor).move_to([-3.7, -2.6, 0])
            note_next = label('방향 차이 0 → 회전 명령 0', 30).move_to([0, 2.6, 0])
            b.play(bot.animate.rotate(desired - yaw, about_point=origin), Transform(actual_arrow, aligned), FadeOut(error_arc), change_sentence(current_label, current_label_next), change_sentence(note, note_next), run_time=0.8)
            current_label = current_label_next
            note = note_next
            b.wait(max(0, anchors[4] - anchors[3] - 0.8))
            heading_next = label('기록된 명령 뒤의 실제 움직임', 37).move_to([0, 3.35, 0])
            b.play(Transform(bot, robot(prev)), FadeOut(actual_arrow), FadeOut(target_arrow), FadeOut(current_label), FadeOut(target_label), FadeOut(selected), FadeOut(point), FadeOut(point_label), FadeOut(note), FadeIn(flow), change_sentence(heading, heading_next), run_time=0.5)
            heading = heading_next
            bot.add_updater(lambda m: m.become(robot(ROWS[min(900, round(clock.get_value() * 30))])))
            self.add(actual)
            b.play(clock.animate.set_value(3.5), run_time=1.8, rate_func=linear)
            b.play(clock.animate.set_value(12), run_time=max(0.2, dur[2] - anchors[4] - 2.3), rate_func=linear)
        bot.clear_updaters()
        actual.clear_updaters()
