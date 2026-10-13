from __future__ import annotations

import unittest
import importlib
import sys
import types
from pathlib import Path
from unittest.mock import patch

from core.visual_primitives.design_tokens import (
    COLORS,
    TOKENS,
    contrast_ratio,
    hex_to_linear_rgba,
)


class VisualDesignTokenTests(unittest.TestCase):
    def test_shared_manim_palette_keeps_existing_values(self):
        self.assertEqual(TOKENS["canvas"]["aspect_ratio"], "16:9")
        self.assertEqual(COLORS["background"], "#0B1020")
        self.assertEqual(COLORS["active"], "#FBBF24")
        self.assertEqual(COLORS["result"], "#34D399")
        self.assertEqual(COLORS["secondary_text"], "#8A94A6")

    def test_manim_kit_reads_shared_palette_tokens(self):
        kit_path = (Path(__file__).resolve().parents[1]
                    / "core/manim-robotics-education-skill/templates")
        manim_stub = types.ModuleType("manim")
        manim_stub.Scene = type("Scene", (), {})
        manim_stub.MovingCameraScene = type("MovingCameraScene", (manim_stub.Scene,), {})
        manim_stub.ValueTracker = type("ValueTracker", (), {})
        manim_stub.NORMAL = "NORMAL"
        manim_stub.ORIGIN = (0, 0, 0)
        manim_stub.UP = (0, 1, 0)
        manim_stub.DOWN = (0, -1, 0)
        manim_stub.LEFT = (-1, 0, 0)
        manim_stub.RIGHT = (1, 0, 0)
        manim_stub.UR = (1, 1, 0)
        manim_stub.RIGHT = (1, 0, 0)
        manim_stub.BOLD = "BOLD"
        manim_stub.config = types.SimpleNamespace(frame_width=14.2, frame_height=8.0)
        sys.path.insert(0, str(kit_path))
        try:
            with patch.dict(sys.modules, {"manim": manim_stub}):
                kit = importlib.import_module("manim_kit")
                self.assertEqual(kit.P.bg, COLORS["background"])
                self.assertEqual(kit.P.fg, COLORS["primary_text"])
                self.assertEqual(kit.P.active, COLORS["active"])
        finally:
            sys.path.remove(str(kit_path))
            sys.modules.pop("manim_kit", None)

    def test_bearing_colors_have_semantic_renderer_matches(self):
        self.assertEqual(COLORS["bearing_cage"], "#E6A653")
        self.assertEqual(COLORS["error"], "#F87171")
        self.assertEqual(COLORS["primary_text"], "#F4F7FB")

    def test_critical_preview_typography_floor_and_text_contrast(self):
        self.assertGreaterEqual(TOKENS["typography_1080p"]["minimum_critical_preview_px"], 14)
        background = COLORS["background"]
        self.assertGreaterEqual(contrast_ratio(COLORS["primary_text"], background), 4.5)
        self.assertGreaterEqual(contrast_ratio(COLORS["secondary_text"], background), 4.5)

    def test_srgb_tokens_convert_to_blender_linear_color(self):
        self.assertEqual(hex_to_linear_rgba("#FFFFFF"), (1.0, 1.0, 1.0, 1.0))
        self.assertNotEqual(hex_to_linear_rgba("#808080")[0], 128 / 255)
        with self.assertRaises(ValueError):
            hex_to_linear_rgba("white")


if __name__ == "__main__":
    unittest.main()
