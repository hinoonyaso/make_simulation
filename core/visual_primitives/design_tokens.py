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
    if data.get("canvas", {}).get("aspect_ratio") != "16:9":
        raise ValueError("education design tokens require a 16:9 canvas")
    typography = data.get("typography_1080p", {})
    if typography.get("minimum_critical_preview_px", 0) < 14:
        raise ValueError("critical text must remain at least 14 px in 540p previews")
    return data


TOKENS = load_tokens()
COLORS = TOKENS["colors"]


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
