from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from manim import *

# The compositor contract is specified in 1920x1080 pixel coordinates.  A
# 16:9 logical frame makes 120 px exactly one Manim unit in both directions.
config.frame_width = 16
config.frame_height = 9

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "core" / "manim-robotics-education-skill" / "templates"))
from manim_kit import pipeline, point_p, safe  # noqa: E402


BG = "#F7F9FC"
INK = "#243247"
MUTED = "#8B95A1"
FAINT = "#DDE3EA"
PURPLE = "#7867C5"
LINK2 = "#AAB2BD"
AMBER = "#E6A027"
X_RED = "#E74C3C"
Y_GREEN = "#18874B"
Z_BLUE = "#2379B3"
FONT = "NanumGothic"

TRACE = json.loads((HERE / "output" / "trace.json").read_text(encoding="utf-8"))["frames"]


def text(s: str, size: float = 30, color: str = INK, weight=NORMAL, **kwargs):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kwargs)


def mathtex(s: str, size: float = 40, color: str = INK, **kwargs):
    return MathTex(s, font_size=size, color=color, **kwargs)


def panel(width: float, height: float, color: str = WHITE, stroke: str = FAINT):
    return RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.18,
        fill_color=color,
        fill_opacity=0.96,
        stroke_color=stroke,
        stroke_width=1.4,
    )


def header(scene_number: int, label: str):
    left = VGroup(
        text(f"SCENE {scene_number}", 22, PURPLE, BOLD),
        text(label, 22, INK),
    ).arrange(RIGHT, buff=0.22)
    left.to_edge(LEFT, buff=0.48).set_y(3.82)
    ep = text("EP01  ·  FORWARD KINEMATICS", 20, MUTED, BOLD).to_edge(RIGHT, buff=0.48).set_y(3.82)
    rule = Line([-7.5, 3.46, 0], [7.5, 3.46, 0], color=FAINT, stroke_width=1.4)
    return VGroup(left, ep, rule)


def section_title(kicker: str, title_s: str, subtitle: str | None = None):
    k = text(kicker, 20, PURPLE, BOLD)
    t = text(title_s, 38, INK, BOLD)
    items = [k, t]
    if subtitle:
        items.append(text(subtitle, 23, MUTED))
    g = VGroup(*items).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
    return g


def get_state(frame_tracker: ValueTracker):
    i = int(round(frame_tracker.get_value()))
    return TRACE[max(0, min(len(TRACE) - 1, i))]


def decimal_readout(label_s, getter, unit, color, decimals=1, width=3.8):
    label_mob = text(label_s, 24, INK, BOLD)
    number = DecimalNumber(
        getter(), num_decimal_places=decimals, include_sign=False,
        font_size=31, color=color,
    )
    number.add_updater(lambda m: m.set_value(getter()))
    unit_mob = text(unit, 21, MUTED)
    row = VGroup(label_mob, number, unit_mob)
    label_mob.move_to([-width / 2 + label_mob.width / 2, 0, 0])
    number.move_to([width / 2 - 1.0, 0, 0])
    unit_mob.next_to(number, RIGHT, buff=0.08)
    return row


def planar_arm(frame_tracker: ValueTracker, one_link=False, origin=(-6.55, -1.55), scale=1.45):
    def points():
        st = get_state(frame_tracker)
        ps = st["planar"][:2] if one_link else st["planar"]
        return [np.array([origin[0] + scale * p[0], origin[1] + scale * p[1], 0]) for p in ps]

    axes = VGroup(
        Arrow([origin[0] - 0.15, origin[1], 0], [origin[0] + 5.7, origin[1], 0], buff=0, color=MUTED, stroke_width=2.3, max_tip_length_to_length_ratio=0.025),
        Arrow([origin[0], origin[1] - 0.15, 0], [origin[0], 2.75, 0], buff=0, color=MUTED, stroke_width=2.3, max_tip_length_to_length_ratio=0.035),
        mathtex("x", 27, X_RED).move_to([origin[0] + 5.88, origin[1], 0]),
        mathtex("y", 27, Y_GREEN).move_to([origin[0], 2.95, 0]),
    )
    l1 = always_redraw(lambda: Line(points()[0], points()[1], color=PURPLE, stroke_width=13))
    base = Dot(points()[0], radius=0.105, color=INK)
    shoulder_ring = Circle(radius=0.19, color=PURPLE, stroke_width=3).move_to(points()[0])
    if one_link:
        p = always_redraw(lambda: point_p(points()[1], color=AMBER, label_text="P"))
        return VGroup(axes, l1, base, shoulder_ring, p)
    l2 = always_redraw(lambda: Line(points()[1], points()[2], color=LINK2, stroke_width=13))
    elbow = always_redraw(lambda: VGroup(Dot(points()[1], radius=0.12, color=WHITE), Circle(radius=0.14, color=INK, stroke_width=3).move_to(points()[1])))
    p = always_redraw(lambda: point_p(points()[2], color=AMBER, label_text="P"))
    return VGroup(axes, l1, l2, base, shoulder_ring, elbow, p)


def one_link_annotations(frame_tracker: ValueTracker, origin=(-6.55, -1.55), scale=1.45):
    def p1():
        p = get_state(frame_tracker)["planar"][1]
        return np.array([origin[0] + scale * p[0], origin[1] + scale * p[1], 0])

    alpha_arc = always_redraw(lambda: Arc(
        radius=0.72,
        start_angle=0,
        angle=get_state(frame_tracker)["q_rad"][1],
        arc_center=np.array([origin[0], origin[1], 0]),
        color=PURPLE,
        stroke_width=4,
    ))
    alpha_label = always_redraw(lambda: mathtex("\\alpha", 30, PURPLE).move_to(
        np.array([origin[0], origin[1], 0]) + 0.98 * np.array([
            math.cos(get_state(frame_tracker)["q_rad"][1] / 2),
            math.sin(get_state(frame_tracker)["q_rad"][1] / 2), 0,
        ])
    ))
    radius_arc = Arc(radius=2.9, start_angle=0, angle=PI / 2, arc_center=[origin[0], origin[1], 0], color=FAINT, stroke_width=3)
    radius_label = mathtex("L", 31, PURPLE).move_to([-4.95, 0.35, 0])
    vertical = always_redraw(lambda: DashedLine(p1(), [p1()[0], origin[1], 0], color=Y_GREEN, dash_length=0.12, stroke_width=3))
    horizontal = always_redraw(lambda: DashedLine([origin[0], p1()[1], 0], p1(), color=X_RED, dash_length=0.12, stroke_width=3))
    x_brace = always_redraw(lambda: BraceBetweenPoints([origin[0], origin[1] - 0.18, 0], [p1()[0], origin[1] - 0.18, 0], direction=DOWN, color=X_RED))
    y_brace = always_redraw(lambda: BraceBetweenPoints([p1()[0] + 0.18, origin[1], 0], [p1()[0] + 0.18, p1()[1], 0], direction=RIGHT, color=Y_GREEN))
    return VGroup(alpha_arc, alpha_label, radius_arc, radius_label), VGroup(vertical, horizontal, x_brace, y_brace)


def two_link_annotations(frame_tracker: ValueTracker, origin=(-6.55, -1.55), scale=1.45):
    def p(i):
        q = get_state(frame_tracker)["planar"][i]
        return np.array([origin[0] + scale * q[0], origin[1] + scale * q[1], 0])

    alpha_arc = always_redraw(lambda: Arc(radius=0.66, start_angle=0, angle=get_state(frame_tracker)["q_rad"][1], arc_center=p(0), color=PURPLE, stroke_width=4))
    beta_arc = always_redraw(lambda: Arc(radius=0.5, start_angle=get_state(frame_tracker)["q_rad"][1], angle=get_state(frame_tracker)["q_rad"][2], arc_center=p(1), color=INK, stroke_width=4))
    sum_arc = always_redraw(lambda: Arc(radius=0.92, start_angle=0, angle=get_state(frame_tracker)["q_rad"][1] + get_state(frame_tracker)["q_rad"][2], arc_center=p(0), color=AMBER, stroke_width=4))
    alpha = mathtex("\\alpha", 29, PURPLE).move_to([-5.65, -1.02, 0])
    beta = always_redraw(lambda: mathtex("\\beta", 29, INK).next_to(p(1), UP, buff=0.22))
    total = mathtex("\\alpha+\\beta", 31, AMBER).move_to([-5.1, -0.85, 0])
    projections = always_redraw(lambda: VGroup(
        DashedLine(p(2), [p(2)[0], origin[1], 0], color=Y_GREEN, dash_length=0.12, stroke_width=2.5),
        DashedLine([origin[0], p(2)[1], 0], p(2), color=X_RED, dash_length=0.12, stroke_width=2.5),
    ))
    return VGroup(alpha_arc, beta_arc, sum_arc, alpha, beta, total), projections


class EP01ForwardKinematics(Scene):
    def setup(self):
        super().setup()
        self.camera.background_color = BG
        self.trace_frame = ValueTracker(0)
        self.clock_frame = 0

    def advance(self, target_clock_frame: int, *animations):
        duration = (target_clock_frame - self.clock_frame) / 30.0
        if duration <= 0:
            return
        target_trace = min(target_clock_frame, len(TRACE) - 1)
        self.play(
            self.trace_frame.animate.set_value(target_trace),
            *animations,
            run_time=duration,
            rate_func=linear,
        )
        self.clock_frame = target_clock_frame

    def wipe(self, *groups):
        # Several elements enter as individual FadeIn targets.  Clearing the
        # layer guarantees no child survives a semantic scene boundary.
        self.clear()
        self.add(self.trace_frame)

    def construct(self):
        self.add(self.trace_frame)
        self.scene_1()
        self.scene_2()
        self.scene_3()
        self.scene_4()
        self.scene_5()
        self.scene_6()

    def scene_1(self):
        # The Blender compositor owns x=60..1140, y=190..910. Every item here is
        # either above y=190 or strictly right of x=1190.
        h = header(1, "세 관절각에서 손끝 위치로")
        box = panel(5.25, 5.55).move_to([4.85, -0.12, 0])
        title_g = VGroup(
            text("로봇팔은 관절 각도로", 34, INK, BOLD),
            text("손의 위치를 어떻게 계산할까?", 34, INK, BOLD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([4.75, 2.18, 0])
        divider = Line([2.45, 1.43, 0], [7.25, 1.43, 0], color=FAINT, stroke_width=1.5)
        angle_title = text("JOINT ANGLES", 19, MUTED, BOLD).move_to([3.35, 1.25, 0])
        qrows = VGroup(
            decimal_readout("θ₁  베이스", lambda: get_state(self.trace_frame)["q_deg"][0], "°", PURPLE),
            decimal_readout("θ₂  어깨", lambda: get_state(self.trace_frame)["q_deg"][1], "°", PURPLE),
            decimal_readout("θ₃  팔꿈치", lambda: get_state(self.trace_frame)["q_deg"][2], "°", LINK2),
        ).arrange(DOWN, buff=0.28).move_to([4.78, 0.35, 0])
        ee_title = text("END EFFECTOR  P", 19, MUTED, BOLD).move_to([3.45, -0.73, 0])
        erows = VGroup(
            decimal_readout("x", lambda: get_state(self.trace_frame)["ee"][0], "m", X_RED, 2),
            decimal_readout("y", lambda: get_state(self.trace_frame)["ee"][1], "m", Y_GREEN, 2),
            decimal_readout("z", lambda: get_state(self.trace_frame)["ee"][2], "m", Z_BLUE, 2),
        ).arrange(DOWN, buff=0.22).move_to([4.78, -1.52, 0])
        mode = VGroup(Dot(radius=0.055, color=AMBER), text("계산 trace 재생", 19, MUTED)).arrange(RIGHT, buff=0.12).move_to([4.75, -2.58, 0])
        s = VGroup(h, box, title_g, divider, angle_title, qrows, ee_title, erows, mode)
        self.add(s)
        self.advance(436)

        subtitle = VGroup(
            text("평면의 원리", 27, PURPLE, BOLD),
            mathtex("\\longrightarrow", 38, MUTED),
            text("3차원 손끝 좌표", 27, AMBER, BOLD),
        ).arrange(RIGHT, buff=0.24).move_to([4.82, 1.87, 0])
        if subtitle.width > 4.65:
            subtitle.scale_to_fit_width(4.65)
        self.play(FadeOut(title_g), FadeIn(subtitle), run_time=0.7)
        # The 0.7 s transition is included in B02, so continue to its locked end.
        self.clock_frame += 21
        self.trace_frame.set_value(457)
        self.advance(861)
        self.wipe(s, subtitle)

    def scene_2(self):
        h = header(2, "한 링크의 평면 기하")
        st = section_title("PLANAR IDEA", "원 위의 점을 두 성분으로", "한 번에 한 축씩 읽습니다")
        st.move_to([3.9, 2.75, 0])
        arm = planar_arm(self.trace_frame, one_link=True)
        angle_g, proj_g = one_link_annotations(self.trace_frame)
        alpha_num = decimal_readout("α", lambda: get_state(self.trace_frame)["q_deg"][1], "°", PURPLE, 1, 2.6).move_to([3.2, 1.65, 0])
        planar_xy = VGroup(
            decimal_readout("Pₓ", lambda: get_state(self.trace_frame)["planar"][1][0], "m", X_RED, 2, 2.0),
            decimal_readout("Pᵧ", lambda: get_state(self.trace_frame)["planar"][1][1], "m", Y_GREEN, 2, 2.0),
        ).arrange(RIGHT, buff=0.45)
        radius_card = VGroup(
            panel(4.7, 1.2),
            VGroup(mathtex("\\|OP\\|=L", 34, PURPLE), planar_xy).arrange(DOWN, buff=0.12),
        ).move_to([4.4, 0.75, 0])
        eqx = VGroup(Dot(radius=0.06, color=X_RED), mathtex("x=L\\cos\\alpha", 43, INK)).arrange(RIGHT, buff=0.22).move_to([4.15, -0.55, 0])
        eqy = VGroup(Dot(radius=0.06, color=Y_GREEN), mathtex("y=L\\sin\\alpha", 43, INK)).arrange(RIGHT, buff=0.22).move_to([4.15, -1.55, 0])
        intuition = text("그림자의 길이 = 좌표 성분", 22, MUTED).move_to([4.25, -2.55, 0])
        s = VGroup(h, st, arm, angle_g, alpha_num, radius_card)
        self.add(s)
        self.advance(1010)
        self.advance(1120, Create(angle_g[2]), FadeIn(angle_g[3]))
        self.advance(1266)
        self.add(proj_g)
        self.advance(1390, FadeIn(eqx, shift=UP * 0.12))
        self.advance(1515, FadeIn(eqy, shift=UP * 0.12))
        self.advance(1671, FadeIn(intuition))
        self.wipe(s, proj_g, eqx, eqy, intuition)

    def scene_3(self):
        h = header(3, "두 링크와 누적각")
        st = section_title("PARENT → CHILD", "상대각은 앞의 각도에 더해진다", "부모 관절의 회전은 뒤 링크 전체에 전달됩니다")
        st.move_to([3.7, 2.75, 0])
        arm = planar_arm(self.trace_frame, one_link=False)
        angle_g, projections = two_link_annotations(self.trace_frame)
        relative_card = VGroup(
            panel(4.85, 1.35),
            VGroup(
                VGroup(mathtex("\\beta", 38, INK), text("상대각", 22, MUTED)).arrange(RIGHT, buff=0.18),
                VGroup(text("둘째 링크 방향", 22, MUTED), mathtex("=\\alpha+\\beta", 38, AMBER)).arrange(RIGHT, buff=0.18),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.14),
        ).move_to([4.42, 1.08, 0])
        alpha_live = decimal_readout("α  어깨", lambda: get_state(self.trace_frame)["q_deg"][1], "°", PURPLE, 1).move_to([4.35, -0.02, 0])
        beta_live = decimal_readout("β  팔꿈치", lambda: get_state(self.trace_frame)["q_deg"][2], "°", INK, 1).move_to([4.35, -0.58, 0])
        parent_note = VGroup(
            text("α 회전", 22, PURPLE, BOLD), text("→ 두 링크", 22, INK),
            text("β 회전", 22, INK, BOLD), text("→ 둘째 링크만", 22, INK),
        ).arrange_in_grid(rows=2, cols=2, buff=(0.22, 0.18), cell_alignment=LEFT).move_to([4.3, -1.48, 0])
        eqx = mathtex("x=L_1\\cos\\alpha+L_2\\cos(\\alpha+\\beta)", 35, INK).move_to([4.15, -0.48, 0])
        eqy = mathtex("y=L_1\\sin\\alpha+L_2\\sin(\\alpha+\\beta)", 35, INK).move_to([4.15, -1.31, 0])
        planar_xy = VGroup(
            decimal_readout("Pₓ", lambda: get_state(self.trace_frame)["planar"][2][0], "m", X_RED, 2, 2.0),
            decimal_readout("Pᵧ", lambda: get_state(self.trace_frame)["planar"][2][1], "m", Y_GREEN, 2, 2.0),
        ).arrange(RIGHT, buff=0.5).move_to([4.2, -2.22, 0])
        s = VGroup(h, st, arm, angle_g, relative_card, alpha_live, beta_live)
        self.add(s)
        self.advance(1900)
        self.advance(2151, Indicate(relative_card[1], color=AMBER, scale_factor=1.025))
        self.add(parent_note)
        self.advance(2400, Indicate(parent_note[2:], color=AMBER, scale_factor=1.04))
        self.advance(2510)
        self.clear()
        self.add(self.trace_frame, h, st, arm, angle_g)
        self.add(projections)
        self.advance(2550, FadeIn(eqx, shift=RIGHT * 0.15))
        self.advance(2616, FadeIn(eqy, shift=RIGHT * 0.15))
        self.advance(2640, FadeIn(planar_xy))
        self.advance(2676)
        self.wipe(s, projections, eqx, eqy, planar_xy)

    def scene_4(self):
        # As in Scene 1, the left viewport is deliberately untouched.
        h = header(4, "평면을 3차원으로 세우기")
        box = panel(5.25, 5.55).move_to([4.85, -0.12, 0])
        title_g = VGroup(
            text("평면 높이", 25, MUTED),
            mathtex("y_{plane}", 43, Y_GREEN),
            mathtex("\\Longleftrightarrow", 38, MUTED),
            mathtex("z-h", 43, Z_BLUE),
        ).arrange(RIGHT, buff=0.2).move_to([4.85, 2.1, 0])
        hrow = VGroup(text("어깨 높이", 22, MUTED), mathtex("h=0.6\\,\\mathrm{m}", 34, INK)).arrange(RIGHT, buff=0.2).move_to([4.75, 1.38, 0])
        divider = Line([2.45, 1.05, 0], [7.25, 1.05, 0], color=FAINT, stroke_width=1.5)
        angle_title = text("3D JOINT ANGLES", 19, MUTED, BOLD).move_to([3.5, 0.74, 0])
        qrows = VGroup(
            decimal_readout("θ₁  yaw", lambda: get_state(self.trace_frame)["q_deg"][0], "°", PURPLE),
            decimal_readout("θ₂  shoulder", lambda: get_state(self.trace_frame)["q_deg"][1], "°", PURPLE),
            decimal_readout("θ₃  elbow", lambda: get_state(self.trace_frame)["q_deg"][2], "°", LINK2),
        ).arrange(DOWN, buff=0.24).move_to([4.78, -0.1, 0])
        ee = VGroup(
            text("FRAME {3} ORIGIN = P", 19, AMBER, BOLD),
            decimal_readout("x", lambda: get_state(self.trace_frame)["ee"][0], "m", X_RED, 2),
            decimal_readout("y", lambda: get_state(self.trace_frame)["ee"][1], "m", Y_GREEN, 2),
            decimal_readout("z", lambda: get_state(self.trace_frame)["ee"][2], "m", Z_BLUE, 2),
        ).arrange(DOWN, buff=0.2).move_to([4.78, -1.76, 0])
        s = VGroup(h, box, title_g, hrow, divider, angle_title, qrows, ee)
        self.add(s)
        self.advance(3030, Indicate(title_g, color=Z_BLUE, scale_factor=1.025))
        self.advance(3231)
        self.remove(title_g, hrow)
        dependency = VGroup(
            text("어깨 θ₂", 23, PURPLE, BOLD), text("두 링크", 22, INK),
            text("팔꿈치 θ₃", 23, INK, BOLD), text("마지막 링크 + {3}", 22, INK),
        ).arrange_in_grid(rows=2, cols=2, buff=(0.22, 0.16), cell_alignment=LEFT).move_to([4.75, 1.95, 0])
        self.add(dependency)
        self.advance(3500, Indicate(dependency[0:2], color=PURPLE, scale_factor=1.035))
        self.advance(3650, Indicate(dependency[2:4], color=AMBER, scale_factor=1.035))
        self.advance(3786, Indicate(ee[0], color=AMBER, scale_factor=1.04))
        self.wipe(s, dependency)

    def scene_5(self):
        h = header(5, "좌표계 체인과 동차변환")
        title_g = section_title("COLUMN VECTORS", "자식 좌표를 부모 좌표로 표현", "좌표 변환은 오른쪽 행렬부터 적용합니다")
        title_g.move_to([0, 2.85, 0])
        notation = mathtex("T_{ij}={}^iT_j", 27, MUTED).move_to([6.25, 2.75, 0])
        frames = VGroup(*[
            VGroup(Circle(radius=0.31, color=(AMBER if i == 3 else PURPLE), stroke_width=3), mathtex(f"\\{{{i}\\}}", 27, AMBER if i == 3 else INK))
            for i in range(4)
        ]).arrange(RIGHT, buff=1.32).move_to([0, 1.72, 0])
        arrows = VGroup(*[
            Arrow(frames[i].get_right(), frames[i + 1].get_left(), buff=0.1, color=MUTED, stroke_width=2.5, max_tip_length_to_length_ratio=0.13)
            for i in range(3)
        ])
        blocks = VGroup(
            VGroup(panel(4.25, 0.9), mathtex("T_{01}=T_z(h)R_z(\\theta_1)", 31, INK)),
            VGroup(panel(4.25, 0.9), mathtex("T_{12}=R_y(-\\theta_2)T_x(L_1)", 31, INK)),
            VGroup(panel(4.25, 0.9), mathtex("T_{23}=R_y(-\\theta_3)T_x(L_2)", 31, INK)),
        ).arrange(DOWN, buff=0.16).move_to([-3.9, -0.3, 0])
        meanings = VGroup(
            text("높이 h · 베이스 yaw", 21, MUTED),
            text("어깨 pitch · 링크 1", 21, MUTED),
            text("팔꿈치 pitch · 링크 2", 21, MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.64).move_to([3.0, -0.3, 0])
        chain_eq = mathtex("T_{03}=T_{01}T_{12}T_{23}", 48, INK).move_to([2.95, -2.03, 0])
        s = VGroup(h, title_g, notation, frames, arrows)
        self.add(s)
        self.advance(3930, FadeIn(blocks[0], shift=RIGHT * 0.12), FadeIn(meanings[0]))
        self.advance(4070, FadeIn(blocks[1], shift=RIGHT * 0.12), FadeIn(meanings[1]))
        self.advance(4210, FadeIn(blocks[2], shift=RIGHT * 0.12), FadeIn(meanings[2]))
        self.advance(4326, FadeIn(chain_eq, shift=UP * 0.12))

        chain_eq.scale(0.72).move_to([0, 2.65, 0])
        self.clear()
        h_result = header(5, "좌표계 체인과 동차변환")
        self.add(self.trace_frame, h_result, chain_eq)
        origin_eq = mathtex("\\begin{bmatrix}p_{EE}\\\\1\\end{bmatrix}=T_{03}\\begin{bmatrix}0\\\\0\\\\0\\\\1\\end{bmatrix}", 38, INK).move_to([0, 1.38, 0])
        r_eq = mathtex("r=L_1\\cos\\theta_2+L_2\\cos(\\theta_2+\\theta_3)", 38, PURPLE).move_to([0, 0.05, 0])
        xy = VGroup(
            mathtex("x=r\\cos\\theta_1", 39, X_RED),
            mathtex("y=r\\sin\\theta_1", 39, Y_GREEN),
        ).arrange(RIGHT, buff=1.0).move_to([0, -0.78, 0])
        z_eq = mathtex("z=h+L_1\\sin\\theta_2+L_2\\sin(\\theta_2+\\theta_3)", 38, Z_BLUE).move_to([0, -1.65, 0])
        numeric = VGroup(
            text("연속 자세", 21, MUTED),
            mathtex("(35^\\circ,25^\\circ,-40^\\circ)", 31, INK),
            mathtex("p_{EE}=(2.67,\\ 1.87,\\ 1.06)^T\\,\\mathrm{m}", 36, AMBER),
        ).arrange(RIGHT, buff=0.28).move_to([0, -2.65, 0])
        self.advance(4430, FadeIn(origin_eq, shift=UP * 0.1))
        self.advance(4560, FadeIn(r_eq, shift=UP * 0.1))
        self.advance(4680, FadeIn(xy, shift=UP * 0.1))
        self.advance(4800, FadeIn(z_eq, shift=UP * 0.1))
        self.advance(4806, FadeIn(numeric, shift=UP * 0.1))
        self.advance(4866)
        self.wipe(s, h_result, chain_eq, origin_eq, r_eq, xy, z_eq, numeric)

    def scene_6(self):
        h = header(6, "순기구학 한눈에 보기")
        title_g = section_title("RECAP", "관절각에서 손끝 좌표까지", "같은 계산을 한 줄로 압축합니다")
        title_g.move_to([0, 2.75, 0])
        flow = pipeline(
            ["관절각", "변환 체인", "순기구학", "손끝 (x, y, z)"],
            colors=[PURPLE, PURPLE, INK, AMBER],
            gap=0.55,
        ).scale(1.08).move_to([0, 0.75, 0])
        for mob in flow.get_family():
            if isinstance(mob, RoundedRectangle):
                mob.set_fill(BG, opacity=0.98).set_stroke(FAINT, width=1.5)
            if isinstance(mob, Text):
                mob.set_color(INK)
        arrows = VGroup(*[m for m in flow.get_family() if isinstance(m, Arrow)])
        fixed = VGroup(
            point_p(ORIGIN, color=AMBER, label_text="P"),
            mathtex("(x,y,z)=(2.67,\\ 1.87,\\ 1.06)\\,\\mathrm{m}", 43, INK),
        ).arrange(RIGHT, buff=0.42).move_to([0, -0.85, 0])
        conclusion = VGroup(
            text("세 관절각", 27, PURPLE, BOLD),
            mathtex("\\longrightarrow", 38, MUTED),
            text("손이 지금 어디에 있는가", 29, INK, BOLD),
        ).arrange(RIGHT, buff=0.28).move_to([0, -2.15, 0])
        s = VGroup(h, title_g, flow, fixed)
        self.add(s)
        self.advance(5000, LaggedStart(*[Indicate(a, color=AMBER, scale_factor=1.05) for a in arrows], lag_ratio=0.28))
        self.advance(5141)
        self.advance(5230, FadeIn(conclusion, shift=UP * 0.12))
        self.advance(5351, Indicate(fixed, color=AMBER, scale_factor=1.025))


class EP01DensePreview(EP01ForwardKinematics):
    """Fast review target for the densest transform derivation."""

    def construct(self):
        self.add(self.trace_frame)
        self.clock_frame = 3786
        self.trace_frame.set_value(3786)
        self.scene_5()
