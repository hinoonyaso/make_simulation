from __future__ import annotations
from dataclasses import dataclass
import math
import os
from pathlib import Path
import sys
from manim import *
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from core.visual_primitives.design_tokens import (
    COLORS as _COLORS,
    TOKENS as _DESIGN,
    get_visual_profile,
    layout_region,
    profile_color,
    recommended_motion,
)
from core.visual_primitives.font_support import discover_manim_korean_font

@dataclass(frozen=True)
class Palette:
    bg: str = _COLORS["background"]
    fg: str = _COLORS["primary_text"]
    muted: str = _COLORS["secondary_text"]
    faint: str = _COLORS["faint"]
    sensor: str = _COLORS["sensor"]
    active: str = _COLORS["active"]
    result: str = _COLORS["result"]
    error: str = _COLORS["error"]
    learned: str = _COLORS["learned"]
    x: str = _COLORS["axis_x"]
    y: str = _COLORS["axis_y"]
    z: str = _COLORS["axis_z"]

    @classmethod
    def for_profile(cls, profile: str = "technical_dark") -> "Palette":
        p = get_visual_profile(profile)
        return cls(bg=p["background"], fg=p["primary_text"], muted=p["secondary_text"],
                   faint=p["border"], sensor=profile_color("sensor", profile),
                   active=profile_color("active", profile), result=profile_color("result", profile),
                   error=profile_color("error", profile), learned=profile_color("learned", profile),
                   x=profile_color("axis_x", profile), y=profile_color("axis_y", profile),
                   z=profile_color("axis_z", profile))
DEFAULT_PROFILE = os.environ.get("EDU_VISUAL_PROFILE", "technical_dark")
P = Palette.for_profile(DEFAULT_PROFILE)

SEMANTIC = {
    "sensor": P.sensor, "active": P.active, "result": P.result,
    "error": P.error, "learned": P.learned, "x": P.x, "y": P.y, "z": P.z,
}


def palette_for_profile(profile: str = "technical_dark") -> Palette:
    return Palette.for_profile(profile)


def apply_theme(scene: Scene, profile=None, background=None):
    """Apply a named canvas profile and expose its palette to the scene."""
    profile = profile or DEFAULT_PROFILE
    palette = palette_for_profile(profile)
    scene.visual_profile = profile
    scene.palette = palette
    scene.camera.background_color = background or palette.bg
    return palette


def txt(text, size=36, color=None, font=None, weight=NORMAL, profile=None):
    palette = palette_for_profile(profile) if profile else P
    color = color or palette.fg
    if font is None:
        font = discover_manim_korean_font(text) if any("\uac00" <= ch <= "\ud7a3" for ch in text) else "NanumGothic"
    return Text(text, font=font, font_size=size, color=color, weight=weight)


def title(text, size=54, profile=None):
    return txt(text, size=size, weight=BOLD, profile=profile)


def muted(text, size=30, profile=None):
    palette = palette_for_profile(profile) if profile else P
    return txt(text, size=size, color=palette.muted)


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


def semantic_tex(tex, mapping=None, font_size=50, profile=None):
    palette = palette_for_profile(profile) if profile else P
    eq = MathTex(tex, font_size=font_size, color=palette.fg)
    mapping = mapping or {}
    for token, role in mapping.items():
        color = getattr(palette, role, SEMANTIC.get(role, role))
        try: eq.set_color_by_tex(token, color)
        except Exception: pass
    return eq


def copy_to_equation(scene, source, equation_part, run_time=.65):
    scene.play(TransformFromCopy(source, equation_part), run_time=run_time)


def tracker(value=0.0):
    return ValueTracker(value)


def tracked_number(v: ValueTracker, decimals=2, color=P.active, size=40):
    return always_redraw(lambda: DecimalNumber(v.get_value(), num_decimal_places=decimals,
                                                font_size=size, color=color))


def point_p(pos=ORIGIN, color=P.active, label_text="P"):
    dot = Dot(pos, color=color, radius=.075)
    lab = MathTex(label_text, color=color, font_size=40).next_to(dot, UR, buff=.08)
    return VGroup(dot, lab)


def coordinate_axes_2d(x_range=(-4,4,1), y_range=(-3,3,1), tips=True, profile=None):
    palette = palette_for_profile(profile) if profile else P
    ax = Axes(x_range=x_range, y_range=y_range, tips=tips,
              axis_config={"color": palette.muted, "stroke_width": 2})
    return ax


def place_in_layout(mob, preset, region, *, center=True, margin=None):
    """Fit and place a mobject inside a normalized token region."""
    x0, y0, x1, y1 = layout_region(preset, region, config.frame_width, config.frame_height)
    if margin is None:
        margin = _DESIGN["layout"]["safe_margin_fraction"] * min(config.frame_width, config.frame_height)
    if not math.isfinite(margin) or margin < 0:
        raise ValueError("layout margin must be finite and non-negative")
    left, right = -config.frame_width / 2 + x0 + margin, -config.frame_width / 2 + x1 - margin
    bottom, top = -config.frame_height / 2 + y0 + margin, -config.frame_height / 2 + y1 - margin
    if not all(math.isfinite(value) for value in (left, right, bottom, top)):
        raise ValueError("layout frame bounds must be finite")
    if right <= left or top <= bottom:
        raise ValueError("layout region has no usable area after applying margin")
    if mob.width > right - left:
        mob.scale_to_fit_width(right - left)
    if mob.height > top - bottom:
        mob.scale_to_fit_height(top - bottom)
    if center:
        return mob.move_to([(left + right) / 2, (bottom + top) / 2, 0])
    # move_to() aligns object centers. Anchor the actual bounding box instead.
    return mob.shift([left - mob.get_left()[0], top - mob.get_top()[1], 0])


def pipeline(labels, colors=None, gap=.35):
    colors = colors or [P.sensor, P.active, P.result]
    nodes=[]
    for i,t in enumerate(labels):
        c=colors[min(i,len(colors)-1)]
        body=VGroup(Dot(radius=.06,color=c), txt(t,28)).arrange(RIGHT,buff=.12)
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



def production_config(preset="1080p", fps=30):
    presets = {
        "preview": (960, 540),
        "720p": (1280, 720),
        "1080p": (1920, 1080),
        "1440p": (2560, 1440),
    }
    w, h = presets[preset]
    config.pixel_width = w
    config.pixel_height = h
    config.frame_rate = fps
    return (w, h, fps)


def hero(mob, width_ratio=.70, height_ratio=.70):
    """Scale a focal visual to use the frame instead of floating small in empty space."""
    max_w = config.frame_width * width_ratio
    max_h = config.frame_height * height_ratio
    if mob.width < max_w and mob.height < max_h:
        factor = min(max_w / max(mob.width, 1e-6), max_h / max(mob.height, 1e-6))
        mob.scale(factor)
    return safe(mob)


def clean_caption(text, size=36, color=P.fg):
    """Optional in-scene caption; subtitles normally belong in Resolve."""
    return txt(text, size=size, color=color).to_edge(DOWN, buff=.35)

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

# --- V9 source-informed production primitives ---
def state_transform(scene, old, new, run_time=.8, match_tex=False, replace=True):
    """Identity-preserving transition. Prefer over fade-out/fade-in slide replacement."""
    if match_tex and isinstance(old, (Tex, MathTex)) and isinstance(new, (Tex, MathTex)):
        anim = TransformMatchingTex(old, new)
    elif replace:
        anim = ReplacementTransform(old, new)
    else:
        anim = Transform(old, new)
    scene.play(anim, run_time=run_time)
    return new


def stagger(*animations, lag=.08, run_time=None):
    kwargs={"lag_ratio": lag}
    if run_time is not None: kwargs["run_time"] = run_time
    return LaggedStart(*animations, **kwargs)


def top_relations(matrix, k=12, min_abs=None, exclude_diagonal=False):
    """Return strongest matrix relations as (row, col, value) tuples; deterministic density control."""
    import numpy as np
    a=np.asarray(matrix, dtype=float)
    items=[]
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            if exclude_diagonal and i == j: continue
            v=float(a[i,j])
            if min_abs is not None and abs(v) < float(min_abs): continue
            items.append((i,j,v))
    items.sort(key=lambda t: abs(t[2]), reverse=True)
    return items[:max(0,int(k))]


def data_polyline(axes, xy, color=P.active, width=4):
    """Create a plot from supplied data rather than an invented decorative curve."""
    pts=[axes.c2p(float(x), float(y)) for x,y in xy]
    return VMobject(color=color, stroke_width=width).set_points_as_corners(pts)


def named_section(scene, name):
    """Use Manim CE sections when available so expensive videos can be iterated in chunks."""
    fn=getattr(scene, "next_section", None)
    if callable(fn): fn(str(name))
    return name


def focus_and_dim(scene, focus_mob, context_mobs=(), opacity=.16, scale=1.04, run_time=.5):
    anims=[focus_mob.animate.scale(scale)]
    anims += [m.animate.set_opacity(opacity) for m in context_mobs if m is not focus_mob]
    scene.play(*anims, run_time=run_time)


def load_trace_json(path):
    """Load the same validated shared trace used by Blender/plots."""
    import json
    from pathlib import Path
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('samples'), list):
        raise ValueError('trace must contain samples[]')
    return data


# --- Pilot-validated primitives (pilots/01_teb_reference) ---
def world_window(width_m, center=(0.0, 0.0)):
    """Metres -> Manim units for a top view that matches studio_utils.top_view(width_m, center).

    Use the same width_m in Blender so a crane-to-top shot can crossfade into this scene pixel-exactly.
    """
    import numpy as np
    k = config.frame_width / float(width_m)
    def W(x, y):
        return np.array([(x - center[0]) * k, (y - center[1]) * k, 0.0])
    W.k = k
    return W


def turtlebot3_top(W, pose, opacity=1.0):
    """Top-view TurtleBot3 Waffle(Pi) icon matching studio_utils.load_turtlebot3 geometry.

    pose = (x, y, yaw) of base_footprint; plate 0.266 m square centred 0.064 m behind the axle.
    """
    k = W.k
    plate = RoundedRectangle(width=.266 * k, height=.266 * k, corner_radius=.03 * k,
                             fill_color="#4A4F57", fill_opacity=1, stroke_color="#7B828D", stroke_width=2)
    plate.shift(LEFT * .064 * k)
    deck = RoundedRectangle(width=.20 * k, height=.20 * k, corner_radius=.02 * k,
                            fill_color="#2E3238", fill_opacity=1, stroke_width=0).shift(LEFT * .064 * k)
    lidar = Circle(radius=.035 * k, fill_color="#16181C", fill_opacity=1, stroke_color="#5C636E",
                   stroke_width=1.5).shift(LEFT * .064 * k)
    wheel = RoundedRectangle(width=.066 * k, height=.022 * k, corner_radius=.008 * k,
                             fill_color="#0E0F12", fill_opacity=1, stroke_width=0)
    front = Line(UP * .10 * k, DOWN * .10 * k, color="#9AA3AF", stroke_width=3).shift(RIGHT * .066 * k)
    g = VGroup(wheel.copy().shift(UP * .144 * k), wheel.copy().shift(DOWN * .144 * k), plate, deck, lidar, front)
    g.rotate(pose[2], about_point=ORIGIN).shift(W(pose[0], pose[1]))
    return g.set_opacity(opacity) if opacity < 1 else g


def beat_seconds(manifest_path, *beat_ids):
    """Measured beat lengths (seconds) from visual_manifest.json after narration sync."""
    import json
    from pathlib import Path
    beats = {b["id"]: float(b["sec"]) for b in json.loads(Path(manifest_path).read_text(encoding="utf-8"))["beats"]}
    return [beats[i] for i in beat_ids]


class BeatClock:
    """Spend exactly one beat's narrated length: play animations, then wait out the remainder.

    with BeatClock(scene, 9.6) as beat:
        beat.play(anim, run_time=2.0)
    If the designed run_times exceed the beat, they are compressed proportionally.
    """
    def __init__(self, scene, seconds, designed=None):
        self.scene, self.seconds, self.used = scene, float(seconds), 0.0
        self.scale = min(1.0, self.seconds / designed) if designed else 1.0

    def __enter__(self):
        return self

    def play(self, *anims, run_time=1.0, **kw):
        rt = run_time * self.scale
        self.scene.play(*anims, run_time=rt, **kw)
        self.used += rt

    def wait(self, seconds):
        rt = seconds * self.scale
        if rt > 0:
            self.scene.wait(rt)
            self.used += rt

    def __exit__(self, *exc):
        rest = self.seconds - self.used
        if rest > 1e-3 and exc[0] is None:
            self.scene.wait(rest)
        return False
