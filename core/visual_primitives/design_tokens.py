"""Shared renderer-neutral visual roles for Blender, Manim, and QA."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

TOKEN_PATH = Path(__file__).with_name("design_tokens.json")
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_tokens(path: Path = TOKEN_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "visual-design-tokens/v1":
        raise ValueError("unsupported design token schema")
    colors = data.get("colors", {})
    if not colors or any(not isinstance(value, str) or not _HEX.fullmatch(value)
                         for value in colors.values()):
        raise ValueError("design token colors must be #RRGGBB values")
    required_colors = {"background", "primary_text", "secondary_text", "sensor", "active",
                       "result", "error", "learned", "input", "output", "warning",
                       "axis_x", "axis_y", "axis_z", "neutral"}
    if not required_colors.issubset(colors):
        raise ValueError(f"design tokens missing semantic colors: {sorted(required_colors - set(colors))}")
    if data.get("canvas", {}).get("aspect_ratio") != "16:9":
        raise ValueError("education design tokens require a 16:9 canvas")
    typography = data.get("typography_1080p", {})
    if typography.get("minimum_critical_preview_px", 0) < 14:
        raise ValueError("critical text must remain at least 14 px in 540p previews")
    profiles = data.get("visual_profiles", {})
    required_profiles = {"studio_light", "technical_dark"}
    if not required_profiles.issubset(profiles):
        raise ValueError(f"visual profiles must include {sorted(required_profiles)}")

    def contrast(foreground: str, background: str) -> float:
        def luminance(value: str) -> float:
            rgb = tuple(int(value[index:index + 2], 16) / 255 for index in (1, 3, 5))
            linear = [channel / 12.92 if channel <= 0.04045
                      else ((channel + 0.055) / 1.055) ** 2.4 for channel in rgb]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
        lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
        return (lighter + 0.05) / (darker + 0.05)

    for name, profile in profiles.items():
        for role in ("background", "surface", "primary_text", "secondary_text", "muted_text",
                     "border", "divider", "neutral_geometry", "floor"):
            value = profile.get(role)
            if not isinstance(value, str) or not _HEX.fullmatch(value):
                raise ValueError(f"visual profile {name!r} requires valid {role} color")
        if contrast(profile["primary_text"], profile["background"]) < 4.5:
            raise ValueError(f"visual profile {name!r} primary text contrast is below 4.5:1")
        if contrast(profile["secondary_text"], profile["background"]) < 4.5:
            raise ValueError(f"visual profile {name!r} secondary text contrast is below 4.5:1")
        for role, value in {**{k: v for k, v in profile.items() if isinstance(v, str)},
                            **profile.get("semantic_colors", {})}.items():
            if not _HEX.fullmatch(value):
                raise ValueError(f"visual profile {name!r} has invalid color {role!r}")
    layout = data.get("layout", {})
    if not layout.get("presets"):
        raise ValueError("at least one layout preset is required")
    for preset, regions in layout["presets"].items():
        for region, rect in regions.items():
            if (not isinstance(rect, list) or len(rect) != 4
                    or any(not isinstance(v, (int, float)) or not 0 <= v <= 1 for v in rect)
                    or rect[0] >= rect[2] or rect[1] >= rect[3]):
                raise ValueError(f"invalid normalized region {preset}.{region}")
    for name, interval in data.get("motion_seconds", {}).items():
        if (not isinstance(interval, list) or len(interval) != 2
                or any(not isinstance(v, (int, float)) or v < 0 for v in interval)
                or interval[0] > interval[1]):
            raise ValueError(f"invalid recommended motion interval: {name}")
    material_roles = data.get("material_roles", {})
    for name, values in material_roles.items():
        for key in ("metallic", "roughness", "transmission"):
            if key in values and (not isinstance(values[key], (int, float)) or not 0 <= values[key] <= 1):
                raise ValueError(f"invalid material property: {name}.{key}")
    return data


TOKENS = load_tokens()
COLORS = TOKENS["colors"]
VISUAL_PROFILES = TOKENS["visual_profiles"]
LAYOUT_PRESETS = TOKENS["layout"]["presets"]

_GOAL_PROFILE = {
    "spatial_geometry": "studio_light",
    "robot_motion": "studio_light",
    "physical_parts": "studio_light",
    "assembly": "studio_light",
    "equation": "technical_dark",
    "algorithm": "technical_dark",
    "data_flow": "technical_dark",
    "graph": "technical_dark",
    "matrix": "technical_dark",
}


def get_visual_profile(name: str) -> dict[str, Any]:
    """Return a named profile; profile choice is explicit and renderer independent."""
    try:
        return VISUAL_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"unknown visual profile {name!r}; choose {sorted(VISUAL_PROFILES)}") from exc


def recommend_visual_profile(visual_goal: str) -> str:
    """Return a starting recommendation, not a renderer or scene mandate."""
    try:
        return _GOAL_PROFILE[visual_goal]
    except KeyError as exc:
        raise ValueError(f"unknown visual goal {visual_goal!r}; choose {sorted(_GOAL_PROFILE)}") from exc


def profile_color(role: str, profile: str = "technical_dark") -> str:
    """Resolve profile canvas roles first, then shared semantic colors."""
    selected = get_visual_profile(profile)
    if role in selected.get("semantic_colors", {}):
        return selected["semantic_colors"][role]
    if role in selected:
        return selected[role]
    if role in COLORS:
        return COLORS[role]
    aliases = {"text": "primary_text", "muted": "muted_text", "bg": "background"}
    resolved = aliases.get(role)
    if resolved and resolved in selected:
        return selected[resolved]
    raise KeyError(f"unknown color role {role!r} for {profile}")


def layout_region(name: str, region: str, width: float, height: float) -> tuple[float, float, float, float]:
    """Map a normalized layout hint to pixel-space bounds (origin at lower-left)."""
    try:
        x0, y0, x1, y1 = LAYOUT_PRESETS[name][region]
    except KeyError as exc:
        raise ValueError(f"unknown layout region {name}.{region}") from exc
    return x0 * width, y0 * height, x1 * width, y1 * height


def recommended_motion(name: str) -> tuple[float, float]:
    """Return advisory timing bounds; narration/events remain the timing authority."""
    try:
        low, high = TOKENS["motion_seconds"][name]
    except KeyError as exc:
        raise ValueError(f"unknown motion token {name!r}") from exc
    return float(low), float(high)


def hex_to_rgba(value: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    if not _HEX.fullmatch(value):
        raise ValueError(f"invalid RGB hex color: {value!r}")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)) + (alpha,)


def hex_to_linear_rgba(value: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    """Convert display-referred sRGB tokens to Blender scene-linear channels."""
    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return tuple(linear(channel) for channel in hex_to_rgba(value)[:3]) + (alpha,)


def relative_luminance(value: str) -> float:
    channels = hex_to_rgba(value)[:3]
    linear = [channel / 12.92 if channel <= 0.04045
              else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted((relative_luminance(foreground), relative_luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)
