"""Cross-platform Korean font discovery and Hangul cmap validation."""
from __future__ import annotations

import os
import re
import struct
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Callable, Mapping

FONT_ENV = "BEARING_KOREAN_FONT"
COMMON_FONT_ENV = "EDU_KOREAN_FONT"
MANIM_FONT_ENV = "EDU_MANIM_FONT"
_HANGUL_SYLLABLES = range(0xAC00, 0xD7A4)


def _u16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def _font_cmap_subtables(data: bytes) -> list[int]:
    face_offset = 0
    if data[:4] == b"ttcf":
        if _u32(data, 8) < 1:
            return []
        face_offset = _u32(data, 12)
    num_tables = _u16(data, face_offset + 4)
    cmap_offset = None
    cmap_length = None
    for index in range(num_tables):
        record = face_offset + 12 + index * 16
        if data[record:record + 4] == b"cmap":
            cmap_offset = _u32(data, record + 8)
            cmap_length = _u32(data, record + 12)
            break
    if cmap_offset is None or cmap_length is None:
        return []
    if cmap_offset + cmap_length > len(data):
        return []

    subtables: list[tuple[int, int]] = []
    for index in range(_u16(data, cmap_offset + 2)):
        record = cmap_offset + 4 + index * 8
        platform_id = _u16(data, record)
        encoding_id = _u16(data, record + 2)
        relative_offset = _u32(data, record + 4)
        subtable = cmap_offset + relative_offset
        if subtable >= cmap_offset + cmap_length:
            continue
        fmt = _u16(data, subtable)
        if fmt in (4, 12) and (platform_id == 0 or
                                (platform_id == 3 and encoding_id in (1, 10))):
            subtables.append((0 if fmt == 12 else 1, subtable))
    return [offset for _, offset in sorted(subtables)]


def _has_glyph(data: bytes, subtable: int, codepoint: int) -> bool:
    fmt = _u16(data, subtable)
    if fmt == 12:
        group_count = _u32(data, subtable + 12)
        low, high = 0, group_count
        groups = subtable + 16
        while low < high:
            middle = (low + high) // 2
            record = groups + middle * 12
            start, end, first_glyph = struct.unpack_from(">III", data, record)
            if codepoint < start:
                high = middle
            elif codepoint > end:
                low = middle + 1
            else:
                return first_glyph + codepoint - start != 0
        return False
    if fmt != 4 or codepoint > 0xFFFF:
        return False

    segment_count = _u16(data, subtable + 6) // 2
    end_codes = subtable + 8
    start_codes = end_codes + 2 * segment_count + 2
    deltas = start_codes + 2 * segment_count
    range_offsets = deltas + 2 * segment_count
    for index in range(segment_count):
        end_code = _u16(data, end_codes + 2 * index)
        if codepoint > end_code:
            continue
        start_code = _u16(data, start_codes + 2 * index)
        if codepoint < start_code:
            return False
        delta = struct.unpack_from(">h", data, deltas + 2 * index)[0]
        range_offset = _u16(data, range_offsets + 2 * index)
        if range_offset == 0:
            return (codepoint + delta) & 0xFFFF != 0
        glyph_offset = range_offsets + 2 * index + range_offset + 2 * (codepoint - start_code)
        glyph = _u16(data, glyph_offset)
        return glyph != 0 and (glyph + delta) & 0xFFFF != 0
    return False


def missing_hangul_glyphs(font_path: str | Path, text: str) -> list[str]:
    """Return required Hangul syllables absent from a TTF/OTF/TTC cmap."""
    required = sorted({ord(char) for char in text if ord(char) in _HANGUL_SYLLABLES})
    if not required:
        return []
    try:
        data = Path(font_path).read_bytes()
        subtables = _font_cmap_subtables(data)
        if not subtables:
            return [chr(codepoint) for codepoint in required]
        return [chr(codepoint) for codepoint in required
                if not any(_has_glyph(data, subtable, codepoint) for subtable in subtables)]
    except (OSError, struct.error, IndexError, OverflowError):
        return [chr(codepoint) for codepoint in required]


def _normalize_path(value: str, platform: str) -> str:
    if platform.startswith("win"):
        match = re.match(r"^/mnt/([A-Za-z])/(.*)$", value.replace("\\", "/"))
        if match:
            return f"{match.group(1).upper()}:/{match.group(2)}"
    return value


def _windows_candidates(env: Mapping[str, str]) -> list[str]:
    candidates = [
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\malgunbd.ttf",
        r"C:\Windows\Fonts\NanumGothic.ttf",
        r"C:\Windows\Fonts\NotoSansKR-Regular.otf",
        r"C:\Windows\Fonts\NotoSansCJKkr-Regular.otf",
    ]
    local_app_data = env.get("LOCALAPPDATA")
    if local_app_data:
        font_dir = Path(local_app_data) / "Microsoft" / "Windows" / "Fonts"
        if font_dir.is_dir():
            for path in sorted(font_dir.iterdir()):
                if path.suffix.lower() in {".ttf", ".otf", ".ttc"} and re.search(
                        r"(nanum|malgun|gulim|dotum|notosans.*kr|notosanscjk)",
                        path.name, re.IGNORECASE):
                    candidates.append(str(path))
    return candidates


def _linux_candidates(fontconfig_lookup: Callable[[str], str]) -> list[str]:
    candidates: list[str] = []
    for family in ("NanumGothic:lang=ko", "Noto Sans CJK KR:lang=ko", "Noto Sans KR:lang=ko"):
        found = fontconfig_lookup(family).strip()
        if found:
            candidates.append(found)
    candidates.extend((
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
    ))
    return candidates


def _fontconfig_lookup(family: str) -> str:
    try:
        result = subprocess.run(["fc-match", "-f", "%{file}", family],
                                check=False, capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def discover_korean_font(
    text: str,
    explicit_path: str | None = None,
    *,
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    file_exists: Callable[[str], bool] | None = None,
    coverage_check: Callable[[str, str], list[str]] | None = None,
    fontconfig_lookup: Callable[[str], str] = _fontconfig_lookup,
) -> str:
    """Resolve the font Blender itself can open and reject missing Hangul glyphs."""
    platform = platform or sys.platform
    env = os.environ if env is None else env
    file_exists = file_exists or (lambda path: Path(path).is_file())
    coverage_check = coverage_check or missing_hangul_glyphs
    requested = explicit_path if explicit_path is not None else (
        env.get(COMMON_FONT_ENV, "") or env.get(FONT_ENV, ""))
    if requested:
        path = _normalize_path(requested, platform)
        if not file_exists(path):
            raise FileNotFoundError(
                f"{COMMON_FONT_ENV} / {FONT_ENV} points to a font Blender cannot access: {path!r}; "
                "use a path visible to the Blender process")
        missing = coverage_check(path, text)
        if missing:
            raise ValueError(f"Korean font {path!r} lacks Hangul glyphs: {''.join(missing)}")
        return path

    if platform.startswith("win"):
        candidates = _windows_candidates(env)
    elif platform.startswith("linux"):
        candidates = _linux_candidates(fontconfig_lookup)
    elif platform == "darwin":
        candidates = ["/System/Library/Fonts/AppleSDGothicNeo.ttc",
                      "/System/Library/Fonts/Supplemental/AppleGothic.ttf"]
    else:
        raise RuntimeError(f"Korean font discovery is unsupported on Blender platform {platform!r}")

    seen: set[str] = set()
    for candidate in candidates:
        path = _normalize_path(candidate, platform)
        if path in seen or not file_exists(path):
            continue
        seen.add(path)
        if not coverage_check(path, text):
            return path
    raise RuntimeError(
        "No installed font with all required Korean Hangul glyphs is accessible to Blender. "
        f"Set {COMMON_FONT_ENV} (or legacy {FONT_ENV}) to a readable font file "
        "(for Windows Blender, use a Windows-visible path).")


@lru_cache(maxsize=16)
def _font_path_for_family(family: str, platform: str) -> str:
    if platform.startswith("linux"):
        return _fontconfig_lookup(f"{family}:lang=ko")
    if platform.startswith("win"):
        names = {
            "Malgun Gothic": r"C:\Windows\Fonts\malgun.ttf",
            "NanumGothic": r"C:\Windows\Fonts\NanumGothic.ttf",
            "Noto Sans KR": r"C:\Windows\Fonts\NotoSansKR-Regular.otf",
        }
        path = names.get(family, "")
        return path if Path(path).is_file() else ""
    if platform == "darwin":
        return "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    return ""


def discover_manim_korean_font(
    text: str,
    explicit_family: str | None = None,
    *,
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    font_path_lookup: Callable[[str, str], str] | None = None,
    coverage_check: Callable[[str, str], list[str]] | None = None,
) -> str:
    """Select a Manim font family whose installed file contains the used Hangul.

    EDU_MANIM_FONT is a Manim family name, while EDU_KOREAN_FONT is a Blender
    font file. The legacy Blender-only BEARING_KOREAN_FONT remains supported.
    """
    platform = platform or sys.platform
    env = os.environ if env is None else env
    if not any(ord(char) in _HANGUL_SYLLABLES for char in text):
        return explicit_family or env.get(MANIM_FONT_ENV, "NanumGothic")
    requested = explicit_family if explicit_family is not None else env.get(MANIM_FONT_ENV, "")
    candidates = [requested] if requested else ["NanumGothic", "Noto Sans CJK KR", "Noto Sans KR"]
    lookup = font_path_lookup or _font_path_for_family
    coverage_check = coverage_check or missing_hangul_glyphs
    for family in candidates:
        path = lookup(family, platform)
        if path and not coverage_check(path, text):
            return family
    if requested:
        raise RuntimeError(
            f"Manim font family {requested!r} is unavailable or lacks required Hangul glyphs; "
            f"install it or set {MANIM_FONT_ENV} to an installed family name")
    raise RuntimeError(
        f"No installed Manim font covers the required Hangul; install Nanum Gothic/Noto Sans KR "
        f"or set {MANIM_FONT_ENV} to an installed family name")
