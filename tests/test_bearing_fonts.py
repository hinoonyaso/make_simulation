from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from core.visual_primitives.font_support import (
    COMMON_FONT_ENV,
    FONT_ENV,
    MANIM_FONT_ENV,
    discover_korean_font,
    discover_manim_korean_font,
    missing_hangul_glyphs,
)


def make_format4_font(path: Path, codepoints: set[int]) -> None:
    """Write a tiny sfnt containing only a format-4 cmap for coverage tests."""
    entries = sorted(codepoints | {0xFFFF})
    segment_count = len(entries)
    end_codes = b"".join(struct.pack(">H", codepoint) for codepoint in entries)
    start_codes = end_codes
    def signed_delta(codepoint: int) -> int:
        delta = (1 - codepoint) & 0xFFFF
        return delta - 0x10000 if delta >= 0x8000 else delta

    deltas = b"".join(struct.pack(">h", signed_delta(codepoint)) for codepoint in entries)
    range_offsets = b"\x00\x00" * segment_count
    subtable_length = 10 + 8 * segment_count
    subtable = (struct.pack(">HHHH", 4, subtable_length, 0, segment_count * 2)
                + end_codes + b"\x00\x00" + start_codes + deltas + range_offsets)
    cmap = (struct.pack(">HH", 0, 1)
            + struct.pack(">HHI", 3, 1, 12) + subtable)
    header = struct.pack(">IHHHH", 0x00010000, 1, 0, 0, 0)
    table_record = b"cmap" + struct.pack(">III", 0, 28, len(cmap))
    path.write_bytes(header + table_record + cmap)


class BearingFontTests(unittest.TestCase):
    def test_valid_hangul_cmap_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "korean.ttf"
            make_format4_font(path, {ord("한"), ord("글")})
            self.assertEqual(missing_hangul_glyphs(path, "한글 베어링"), ["링", "베", "어"])
            self.assertEqual(missing_hangul_glyphs(path, "한글"), [])

    def test_explicit_font_takes_priority(self):
        calls = []

        def covered(path, _text):
            calls.append(path)
            return []

        selected = discover_korean_font(
            "한글", "/custom/korean.ttf", platform="linux", env={},
            file_exists=lambda path: path == "/custom/korean.ttf", coverage_check=covered,
        )
        self.assertEqual(selected, "/custom/korean.ttf")
        self.assertEqual(calls, ["/custom/korean.ttf"])

    def test_common_font_variable_precedes_legacy_bearing_variable(self):
        selected = discover_korean_font(
            "한글", platform="linux", env={COMMON_FONT_ENV: "/common.ttf", FONT_ENV: "/legacy.ttf"},
            file_exists=lambda _path: True, coverage_check=lambda _path, _text: [],
        )
        self.assertEqual(selected, "/common.ttf")

    def test_invalid_explicit_font_fails_instead_of_falling_back(self):
        with self.assertRaisesRegex(FileNotFoundError, FONT_ENV):
            discover_korean_font("한글", "/missing/font.ttf", platform="linux", env={},
                                 file_exists=lambda _path: False,
                                 coverage_check=lambda _path, _text: [])
        with self.assertRaisesRegex(ValueError, "lacks Hangul glyphs"):
            discover_korean_font("한글", "/font/no-korean.ttf", platform="linux", env={},
                                 file_exists=lambda _path: True,
                                 coverage_check=lambda _path, _text: ["글"])

    def test_windows_blender_normalizes_wsl_mounted_font_path(self):
        selected = discover_korean_font(
            "한글", platform="win32", env={FONT_ENV: "/mnt/c/Windows/Fonts/malgun.ttf"},
            file_exists=lambda path: path == "C:/Windows/Fonts/malgun.ttf",
            coverage_check=lambda _path, _text: [],
        )
        self.assertEqual(selected, "C:/Windows/Fonts/malgun.ttf")

    def test_linux_prefers_fontconfig_korean_family_with_coverage(self):
        selected = discover_korean_font(
            "한글", platform="linux", env={}, file_exists=lambda path: path == "/fonts/nanum.ttf",
            coverage_check=lambda _path, _text: [],
            fontconfig_lookup=lambda family: "/fonts/nanum.ttf" if family.startswith("Nanum") else "",
        )
        self.assertEqual(selected, "/fonts/nanum.ttf")

    def test_candidate_without_required_hangul_is_skipped(self):
        selected = discover_korean_font(
            "한글", platform="win32", env={},
            file_exists=lambda path: "malgun" in path.lower(),
            coverage_check=lambda path, _text: ["한"] if "malgun.ttf" in path.lower() else [],
        )
        self.assertIn("malgunbd.ttf", selected.lower())

    def test_no_supported_font_fails_with_actionable_message(self):
        with self.assertRaisesRegex(RuntimeError, "legacy BEARING_KOREAN_FONT"):
            discover_korean_font("한글", platform="linux", env={}, file_exists=lambda _path: False,
                                 coverage_check=lambda _path, _text: [], fontconfig_lookup=lambda _family: "")

    def test_manim_family_requires_installed_font_and_hangul_coverage(self):
        calls = []

        def lookup(family, _platform):
            calls.append(family)
            return f"/fonts/{family}.ttf"

        selected = discover_manim_korean_font(
            "한글", platform="linux", env={MANIM_FONT_ENV: "NanumGothic"},
            font_path_lookup=lookup, coverage_check=lambda _path, text: [] if "한" in text else ["글"],
        )
        self.assertEqual(selected, "NanumGothic")
        self.assertEqual(calls, ["NanumGothic"])
        with self.assertRaisesRegex(RuntimeError, MANIM_FONT_ENV):
            discover_manim_korean_font("한글", platform="linux", env={MANIM_FONT_ENV: "Missing"},
                                       font_path_lookup=lambda _family, _platform: "",
                                       coverage_check=lambda _path, _text: [])


if __name__ == "__main__":
    unittest.main()
