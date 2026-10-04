"""Read-only upload-package check. Requires ffprobe; never uploads anything."""
import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def check(package):
    package = Path(package).resolve()
    data = json.loads(package.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Package must be a JSON object")
    for field, limit in (("title", 100), ("description", 5000)):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be nonempty text")
        length = len(value.encode("utf-8")) if field == "description" else len(value)
        if length > limit or "<" in value or ">" in value:
            raise ValueError(f"Invalid {field}: length or angle brackets")
    if data.get("privacy") not in ("private", "unlisted", "public"):
        raise ValueError("privacy must be private, unlisted or public")
    for field in ("made_for_kids", "contains_synthetic_media"):
        if field in data and type(data[field]) is not bool:
            raise ValueError(f"{field} must be boolean")
    tags = data.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise ValueError("tags must be a list of strings")
    if "publish_at" in data:
        when = datetime.fromisoformat(data["publish_at"].replace("Z", "+00:00"))
        if when.tzinfo is None or when <= datetime.now(timezone.utc):
            raise ValueError("publish_at must be a future timestamp with timezone")
        if data["privacy"] != "private":
            raise ValueError("Scheduled uploads require private status")
    files = {}
    for field in ("video", "captions", "thumbnail"):
        if field == "video" or field in data:
            name = data.get(field)
            if not isinstance(name, str) or not name:
                raise ValueError(f"{field} must be a file path")
            path = (package.parent / name).resolve()
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"Missing/empty {field}: {path}")
            files[field] = path
    if "captions" in files:
        if files["captions"].suffix.lower() not in (".srt", ".vtt"):
            raise ValueError("Use timed SRT or VTT captions")
        if "-->" not in files["captions"].read_text(encoding="utf-8-sig"):
            raise ValueError("Caption file has no timed cues")
        if not isinstance(data.get("caption_language"), str) or not data["caption_language"]:
            raise ValueError("caption_language is required for a caption track")
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(files["video"])
    ], capture_output=True, text=True, check=True, timeout=60)
    probe = json.loads(result.stdout)
    kinds = {s.get("codec_type") for s in probe["streams"]}
    if not {"video", "audio"} <= kinds:
        raise ValueError("Narrated video must have video and audio streams")
    duration = float(probe["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Invalid media duration")
    chapters = data.get("chapters", [])
    if not isinstance(chapters, list):
        raise ValueError("chapters must be a list")
    previous = -1
    for chapter in chapters:
        if not isinstance(chapter, dict) or "seconds" not in chapter:
            raise ValueError("Each chapter must be an object with seconds and title")
        seconds = chapter["seconds"]
        if (type(seconds) not in (int, float) or not math.isfinite(seconds)
                or not previous < seconds < duration or not chapter.get("title")):
            raise ValueError("Chapters must have titles and increasing times inside the video")
        previous = seconds
    hashes = {}
    for field, path in {"package": package, **files}.items():
        with path.open("rb") as stream:
            hashes[field] = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"local_check": "passed", "duration_seconds": duration,
            "sha256": hashes, "privacy": data["privacy"],
            "execution_fields_missing": [f for f in ("channel_id", "made_for_kids") if f not in data],
            "limitations": "No upload, authorization, remote eligibility, full decode, subtitle timing or visual-content review performed."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.package), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Preflight failed: {error}\n")
