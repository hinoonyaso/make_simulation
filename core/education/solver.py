"""Optional engineering solver plugin contract; no solver is installed by V13."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class SolverStatus(StrEnum):
    PLANNED = "PLANNED"
    ENVIRONMENT_CHECKED = "ENVIRONMENT_CHECKED"
    EXAMPLE_VALIDATED = "EXAMPLE_VALIDATED"
    RENDER_VALIDATED = "RENDER_VALIDATED"
    PRODUCTION_READY = "PRODUCTION_READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class SolverResult:
    solver_name: str
    solver_version: str | None
    model_name: str
    input_configuration: dict[str, Any]
    units: dict[str, str]
    assumptions: tuple[str, ...]
    boundary_conditions: dict[str, Any]
    provenance: dict[str, Any]
    execution_status: SolverStatus
    output_files: tuple[str, ...]
    validation_summary: tuple[str, ...]
    known_limitations: tuple[str, ...]


class EngineeringSolver(ABC):
    """Adapter API for future isolated solver integrations."""

    @abstractmethod
    def check_environment(self) -> dict[str, Any]: ...

    @abstractmethod
    def validate_input(self, config: dict[str, Any]) -> list[str]: ...

    @abstractmethod
    def execute(self, config: dict[str, Any]) -> SolverResult: ...

    @abstractmethod
    def validate_result(self, result: SolverResult) -> list[str]: ...

    @abstractmethod
    def export_visual_data(self, result: SolverResult) -> dict[str, Any]: ...
