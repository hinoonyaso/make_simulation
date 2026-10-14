from __future__ import annotations

import importlib
import importlib.util
import sys
import unittest
from pathlib import Path

if importlib.util.find_spec("manim") is None:
    raise unittest.SkipTest("Manim layout tests require the sim-render dependency group")

from manim import MathTex, Text, VGroup, config


KIT_PATH = (Path(__file__).resolve().parents[1]
            / "core/manim-robotics-education-skill/templates")
sys.path.insert(0, str(KIT_PATH))
try:
    manim_kit = importlib.import_module("manim_kit")
finally:
    sys.path.remove(str(KIT_PATH))


class PlaceInLayoutTests(unittest.TestCase):
    def setUp(self):
        self.old_size = (config.frame_width, config.frame_height,
                         config.pixel_width, config.pixel_height)

    def tearDown(self):
        (config.frame_width, config.frame_height,
         config.pixel_width, config.pixel_height) = self.old_size

    def assert_inside(self, mob, preset, region, margin=None):
        x0, y0, x1, y1 = manim_kit.layout_region(
            preset, region, config.frame_width, config.frame_height)
        margin = (manim_kit._DESIGN["layout"]["safe_margin_fraction"]
                  * min(config.frame_width, config.frame_height)) if margin is None else margin
        left = -config.frame_width / 2 + x0 + margin
        right = -config.frame_width / 2 + x1 - margin
        bottom = -config.frame_height / 2 + y0 + margin
        top = -config.frame_height / 2 + y1 - margin
        self.assertGreaterEqual(mob.get_left()[0], left - 1e-6)
        self.assertLessEqual(mob.get_right()[0], right + 1e-6)
        self.assertGreaterEqual(mob.get_bottom()[1], bottom - 1e-6)
        self.assertLessEqual(mob.get_top()[1], top + 1e-6)

    def test_top_left_anchors_text_equation_and_group_by_actual_bounds(self):
        for mob in (
            Text("짧은 텍스트", font="NanumGothic"),
            Text("긴 설명 문장이 레이아웃 영역보다 충분히 넓게 이어지는 경우", font="NanumGothic"),
            MathTex(r"\frac{a+b}{c}=x^2"),
            VGroup(Text("A", font="NanumGothic"), MathTex(r"x+y=1")).arrange(),
        ):
            with self.subTest(mobject=type(mob).__name__):
                bounds = manim_kit.layout_region(
                    "equation_geometry", "equation", config.frame_width, config.frame_height)
                margin = (manim_kit._DESIGN["layout"]["safe_margin_fraction"]
                          * min(config.frame_width, config.frame_height))
                fitted = manim_kit.place_in_layout(
                    mob, "equation_geometry", "equation", center=False)
                self.assertAlmostEqual(fitted.get_left()[0], -config.frame_width / 2
                                       + bounds[0] + margin, places=5)
                self.assertAlmostEqual(fitted.get_top()[1], -config.frame_height / 2
                                       + bounds[3] - margin, places=5)
                self.assert_inside(fitted, "equation_geometry", "equation")

    def test_oversized_object_scales_across_frame_aspects_and_delivery_sizes(self):
        for pixel_width, pixel_height, width, height in (
            (960, 540, 14.222, 8.0),
            (1920, 1080, 14.222, 8.0),
            (960, 720, 10.0, 8.0),
            (1920, 1080, 18.0, 10.125),
        ):
            config.pixel_width, config.pixel_height = pixel_width, pixel_height
            config.frame_width, config.frame_height = width, height
            huge = Text("oversized " * 35, font_size=90, font="NanumGothic")
            fitted = manim_kit.place_in_layout(
                huge, "equation_geometry", "equation", center=False)
            self.assert_inside(fitted, "equation_geometry", "equation")

    def test_center_true_remains_centered(self):
        mob = Text("center", font="NanumGothic")
        fitted = manim_kit.place_in_layout(mob, "equation_geometry", "equation", center=True)
        x0, y0, x1, y1 = manim_kit.layout_region(
            "equation_geometry", "equation", config.frame_width, config.frame_height)
        self.assertAlmostEqual(fitted.get_center()[0], -config.frame_width / 2 + (x0 + x1) / 2)
        self.assertAlmostEqual(fitted.get_center()[1], -config.frame_height / 2 + (y0 + y1) / 2)
        self.assert_inside(fitted, "equation_geometry", "equation")

    def test_unusable_margin_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no usable area"):
            manim_kit.place_in_layout(Text("x"), "equation_geometry", "equation",
                                      center=False, margin=100)
        for margin in (-0.1, float("nan"), float("inf")):
            with self.subTest(margin=margin):
                with self.assertRaisesRegex(ValueError, "margin must be finite"):
                    manim_kit.place_in_layout(Text("x"), "equation_geometry", "equation",
                                              center=False, margin=margin)


if __name__ == "__main__":
    unittest.main()
