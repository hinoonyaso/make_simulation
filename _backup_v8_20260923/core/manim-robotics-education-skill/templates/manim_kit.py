from __future__ import annotations
from dataclasses import dataclass
from manim import *

@dataclass(frozen=True)
class Palette:
    bg: str = "#0B1020"
    fg: str = "#F4F7FB"
    muted: str = "#8A94A6"
    faint: str = "#334155"
    sensor: str = "#38BDF8"
    active: str = "#FBBF24"
    result: str = "#34D399"
    error: str = "#F87171"
    learned: str = "#A78BFA"
    x: str = "#EF4444"
    y: str = "#22C55E"
    z: str = "#3B82F6"
P = Palette()

SEMANTIC = {
    "sensor": P.sensor, "active": P.active, "result": P.result,
    "error": P.error, "learned": P.learned, "x": P.x, "y": P.y, "z": P.z,
}


def apply_theme(scene: Scene, background=P.bg):
    scene.camera.background_color = background
    return scene


def txt(text, size=30, color=P.fg, font="NanumGothic", weight=NORMAL):
    return Text(text, font=font, font_size=size, color=color, weight=weight)


def title(text, size=46):
    return txt(text, size=size, weight=BOLD)


def muted(text, size=26):
    return txt(text, size=size, color=P.muted)


def emphasis(mob, color=P.active, scale=1.06):
    return AnimationGroup(mob.animate.set_color(color).scale(scale), lag_ratio=0)


def de_emphasis(mob, opacity=.28):
    return mob.animate.set_opacity(opacity)


def safe(mob, margin=.35):
    fw, fh = config.frame_width - 2*margin, config.frame_height - 2*margin
    if mob.width > fw: mob.scale_to_fit_width(fw)
    if mob.height > fh: mob.scale_to_fit_height(fh)
    return mob


def focus(mob, y=0):
    return mob.move_to([0, y, 0])


def split(left, right, gap=.7):
    return safe(VGroup(left, right).arrange(RIGHT, buff=gap).move_to(ORIGIN))


def stack(*items, gap=.32):
    return safe(VGroup(*items).arrange(DOWN, buff=gap).move_to(ORIGIN))


def semantic_tex(tex, mapping=None, font_size=44):
    eq = MathTex(tex, font_size=font_size, color=P.fg)
    mapping = mapping or {}
    for token, role in mapping.items():
        color = SEMANTIC.get(role, role)
        try: eq.set_color_by_tex(token, color)
        except Exception: pass
    return eq


def copy_to_equation(scene, source, equation_part, run_time=.65):
    scene.play(TransformFromCopy(source, equation_part), run_time=run_time)


def tracker(value=0.0):
    return ValueTracker(value)


def tracked_number(v: ValueTracker, decimals=2, color=P.active, size=34):
    return always_redraw(lambda: DecimalNumber(v.get_value(), num_decimal_places=decimals,
                                                font_size=size, color=color))


def point_p(pos=ORIGIN, color=P.active, label_text="P"):
    dot = Dot(pos, color=color, radius=.075)
    lab = MathTex(label_text, color=color, font_size=34).next_to(dot, UR, buff=.08)
    return VGroup(dot, lab)


def coordinate_axes_2d(x_range=(-4,4,1), y_range=(-3,3,1), tips=True):
    ax = Axes(x_range=x_range, y_range=y_range, tips=tips,
              axis_config={"color": P.muted, "stroke_width": 2})
    return ax


def pipeline(labels, colors=None, gap=.35):
    colors = colors or [P.sensor, P.active, P.result]
    nodes=[]
    for i,t in enumerate(labels):
        c=colors[min(i,len(colors)-1)]
        body=VGroup(Dot(radius=.055,color=c), txt(t,22)).arrange(RIGHT,buff=.12)
        box=RoundedRectangle(width=body.width+.34,height=body.height+.24,corner_radius=.12,
                             stroke_color=P.faint,stroke_width=1.5,fill_color=P.bg,fill_opacity=.96)
        nodes.append(VGroup(box,body))
    row=VGroup(*nodes).arrange(RIGHT,buff=gap)
    arrows=VGroup(*[Arrow(a.get_right(),b.get_left(),buff=.08,color=P.muted,stroke_width=2.5,
                               max_tip_length_to_length_ratio=.12) for a,b in zip(nodes,nodes[1:])])
    return safe(VGroup(row,arrows))


def dim_except(group, keep, opacity=.18):
    anims=[]
    keep_ids={id(x) for x in (keep if isinstance(keep,(list,tuple,set)) else [keep])}
    for mob in group:
        if id(mob) not in keep_ids: anims.append(mob.animate.set_opacity(opacity))
    return AnimationGroup(*anims, lag_ratio=0)


class VisualReasoningScene(MovingCameraScene):
    """Small base class: theme + deliberate pauses + camera focus helper."""
    def setup(self):
        super().setup()
        apply_theme(self)

    def beat(self, *animations, run_time=.8, pause=.15):
        if animations: self.play(*animations, run_time=run_time)
        if pause: self.wait(pause)

    def camera_focus(self, mob, width=None, run_time=.8):
        frame=self.camera.frame
        target_width = width or max(mob.width*1.35, 2.0)
        self.play(frame.animate.move_to(mob).set(width=target_width), run_time=run_time)

# compact aliases
label=txt
