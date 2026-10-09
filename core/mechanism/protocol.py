"""Small common adapter interface; domain trace contracts stay separate."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class MechanismRequest:
    topic: str
    options: dict[str, Any] = field(default_factory=dict)


class MechanismAdapter(Protocol):
    """An adapter owns domain execution and its evidence-aware validation."""

    def describe_capability(self) -> dict[str, Any]: ...
    def prepare(self, request: MechanismRequest) -> dict[str, Any]: ...
    def execute(self, config: dict[str, Any]) -> dict[str, Any]: ...
    def validate(self, trace: dict[str, Any]) -> list[str]: ...
    def build_visual_plan(self, trace: dict[str, Any]) -> dict[str, Any]: ...
    def render(self, plan: dict[str, Any], manifest: dict[str, Any], output: Path) -> Path: ...
