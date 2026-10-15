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
    get_visual_profile,
    hex_to_linear_rgba,
    layout_region,
    profile_color,
    recommend_visual_profile,
    recommended_motion,
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
                light = kit.Palette.for_profile("studio_light")
                self.assertEqual(light.bg, get_visual_profile("studio_light")["background"])
                self.assertEqual(light.active, profile_color("active", "studio_light"))
                self.assertNotEqual(light.active, kit.P.active)
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

    def test_visual_profiles_are_distinct_and_meet_text_contrast(self):
        light = get_visual_profile("studio_light")
        dark = get_visual_profile("technical_dark")
        self.assertNotEqual(light["background"], dark["background"])
        for profile in (light, dark):
            self.assertGreaterEqual(contrast_ratio(profile["primary_text"], profile["background"]), 4.5)
            self.assertGreaterEqual(contrast_ratio(profile["secondary_text"], profile["background"]), 4.5)
        self.assertEqual(
            profile_color("active", "studio_light"),
            get_visual_profile("studio_light")["semantic_colors"]["active"],
        )

    def test_visual_goal_recommendation_does_not_select_a_renderer(self):
        self.assertEqual(recommend_visual_profile("spatial_geometry"), "studio_light")
        self.assertEqual(recommend_visual_profile("algorithm"), "technical_dark")
        with self.assertRaisesRegex(ValueError, "unknown visual goal"):
            recommend_visual_profile("arbitrary")

    def test_layout_and_motion_tokens_are_advisory_ranges(self):
        bounds = layout_region("equation_geometry", "equation", 14.2, 8.0)
        self.assertAlmostEqual(bounds[0], 8.52)
        self.assertAlmostEqual(bounds[1], 1.44)
        self.assertAlmostEqual(bounds[2], 13.348)
        self.assertAlmostEqual(bounds[3], 6.4)
        low, high = recommended_motion("state_transition")
        self.assertLessEqual(low, high)
        self.assertGreaterEqual(high, 0.4)


if __name__ == "__main__":
    unittest.main()
