"""Validated, solver-optional input contract for education-first lessons."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

MODES = {"concept_visualization", "mathematical_demonstration", "computed_engineering_demonstration"}
EVIDENCE_TYPES = {"conceptual_illustration", "derived_calculation", "computed_result", "measured_data"}


@dataclass(frozen=True)
class LessonSpec:
    topic: str
    question: str
    audience: str
    language: str
    duration_target_sec: int
    learning_objectives: tuple[str, ...]
    modes: tuple[str, ...]
    visualization: str
    computation_policy: str
    output_profile: str
    solver: str | None = None
    trace: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LessonSpec":
        errors = validate_lesson_spec(raw)
        if errors:
            raise ValueError("invalid lesson spec: " + "; ".join(errors))
        return cls(topic=raw["topic"], question=raw["question"], audience=raw["audience"],
                   language=raw["language"], duration_target_sec=raw["duration_target_sec"],
                   learning_objectives=tuple(raw["learning_objectives"]),
                   modes=tuple(raw.get("modes", ["concept_visualization"])),
                   visualization=raw.get("visualization", "auto"),
                   computation_policy=raw.get("computation_policy", "only_when_needed"),
                   output_profile=raw.get("output_profile", "youtube_education"),
                   solver=raw.get("solver"), trace=raw.get("trace"))

    @classmethod
    def load(cls, path: str | Path) -> "LessonSpec":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def validate_lesson_spec(raw: Any) -> list[str]:
    if not isinstance(raw, dict):
        return ["root must be an object"]
    errors: list[str] = []
    if raw.get("schema") != "education-lesson-spec/v1":
        errors.append("schema must be education-lesson-spec/v1")
    for key in ("topic", "question", "audience", "language"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            errors.append(f"{key} must be a non-empty string")
    duration = raw.get("duration_target_sec")
    if type(duration) is not int or not 1 <= duration <= 3600:
        errors.append("duration_target_sec must be an integer from 1 to 3600")
    objectives = raw.get("learning_objectives")
    if not isinstance(objectives, list) or not objectives or any(not isinstance(x, str) or not x.strip() for x in objectives):
        errors.append("learning_objectives must be a non-empty list of strings")
    modes = raw.get("modes", ["concept_visualization"])
    if not isinstance(modes, list) or not modes or any(mode not in MODES for mode in modes):
        errors.append("modes must contain supported lesson modes")
    elif len(set(modes)) != len(modes):
        errors.append("modes must not contain duplicates")
    if raw.get("computation_policy", "only_when_needed") not in {"only_when_needed", "always", "never"}:
        errors.append("computation_policy must be only_when_needed, always or never")
    if raw.get("evidence_type", "conceptual_illustration") not in EVIDENCE_TYPES:
        errors.append("evidence_type must be a supported evidence type")
    return errors
