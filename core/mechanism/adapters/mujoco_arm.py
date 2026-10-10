"""Adapter around the existing MuJoCo H1 arm runner and V9 trace validator."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from typing import Any

from core.mechanism.protocol import MechanismRequest


class MuJoCoArmAdapter:
    def __init__(self, capability: dict[str, Any] | None = None):
        self.capability = capability or {}
        self.root = Path(__file__).resolve().parents[3]

    def describe_capability(self): return self.capability
    def prepare(self, request: MechanismRequest): return {"topic": request.topic, **request.options}

    def execute(self, config: dict[str, Any]):
        spec = importlib.util.spec_from_file_location("mujoco_adapter", self.root / "core/robotics-simulation/mujoco_adapter.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        model = Path(config.get("model", self.root / "assets/unitree_h1/mjcf/h1_with_hand.xml"))
        output = Path(config["output_dir"])
        self.last_execution_metrics = {}
        return module.run_arm_experiment(model, output, float(config.get("duration", 2.0)),
            float(config.get("timestep", .002)), float(config.get("sample_period", .02)),
            timings=self.last_execution_metrics)

    def validate(self, trace):
        path = self.root / "core/shared-data/validate_trace.py"
        spec = importlib.util.spec_from_file_location("robotics_trace_validator", path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as file:
            json.dump(trace, file)
            file.flush()
            return module.validate(file.name)

    def build_visual_plan(self, trace):
        model = trace.get("model", {})
        return {"kind": "mujoco_arm", "title": "MuJoCo 로봇팔의 관절 상태와 끝단 이동",
                "samples": trace.get("samples", []),
                "joint_names": model.get("joint_names_in_qpos_order", []),
                "trace_schema": trace.get("schema"),
                "evidence": "MuJoCo physics run; fixed base and PD torque control"}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan, Path(manifest["_path"]), output, manifest.get("render_mode", "preview"))
