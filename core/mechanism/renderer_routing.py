"""Deterministic, explainable renderer selection and lightweight runtime checks."""
from __future__ import annotations

import importlib.metadata
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any
from core.mechanism.joint_motion import analyze_joint_motion

VISUAL_GOALS = ("auto", "numerical_explanation", "algorithm_flow", "image_space",
                "motion_3d", "spatial_relationship", "comparative_analysis")

CAPABILITIES = {
    "manim": {"supported_topics": ["quantization", "nms", "mcu_pid", "self_attention", "robot_kinematics", "rag"],
              "supported_trace_schemas": ["mechanism-envelope/v1", "robotics-visual-trace/v1", "ai-mechanism-trace/v1"],
              "visual_goals": ["numerical_explanation", "algorithm_flow", "spatial_relationship", "comparative_analysis"],
              "required_visual_evidence": ["trace-backed values", "mapped storyboard phase"],
              "dimensions": "2d", "runtime": "manim", "supports_preview": True,
              "supports_final": True, "supports_timeline": True, "physics_execution": False},
    "manim_yolo_image_space": {"supported_topics": ["object_detection"], "visual_goals": ["image_space", "algorithm_flow"],
              "supported_trace_schemas": ["object-detection-execution-trace/v1"],
              "required_visual_evidence": ["source image", "image-space boxes", "confidence and NMS trace"],
              "dimensions": "2d_image_space", "runtime": "manim", "supports_preview": True,
              "supports_final": True, "supports_timeline": True, "physics_execution": False},
    "blender_h1_trace_playback": {"supported_topics": ["robot_kinematics"], "visual_goals": ["motion_3d", "spatial_relationship"],
              "supported_trace_schemas": ["robotics-visual-trace/v1"],
              "required_visual_evidence": ["H1 mesh", "recorded joint state", "forward-kinematic pose"],
              "dimensions": "3d_mesh", "runtime": "blender", "required_assets": ["unitree_h1_mjcf", "unitree_h1_mesh_bundle"],
              "supports_preview": True, "supports_final": True, "supports_timeline": True,
              "physics_execution": False},
    "manim+threejs": {"supported_topics": ["rag"], "visual_goals": ["spatial_relationship"],
              "supported_trace_schemas": ["ai-mechanism-trace/v1"],
              "required_visual_evidence": ["recorded query/chunk vectors", "trace-ranked retrieval"],
              "required_assets": ["local Three.js", "Playwright Chromium", "loopback capture"],
              "dimensions": "2d+3d_projection", "runtime": "manim+node+playwright+chromium",
              "supports_preview": True, "supports_final": True, "supports_timeline": True,
              "physics_execution": False},
}


def infer_visual_goal(topic: str, trace: dict[str, Any] | None = None) -> str:
    if topic == "quantization" or topic == "mcu_pid" or topic == "self_attention":
        return "numerical_explanation"
    if topic == "nms":
        return "algorithm_flow"
    if topic == "object_detection":
        return "image_space"
    if topic == "robot_kinematics":
        samples = (trace or {}).get("samples", [])
        if samples and analyze_joint_motion(trace)["motion_detected"]:
            return "motion_3d"
        return "comparative_analysis"
    if topic == "rag":
        data = trace or {}
        has_query = any(item.get("kind") == "query" for item in data.get("inputs", []))
        has_vectors = any(item.get("kind") in {"embedding", "feature_vector"}
                          for item in data.get("intermediate_values", []))
        return "spatial_relationship" if has_query and has_vectors else "algorithm_flow"
    return "algorithm_flow"


def _probe_manim() -> dict[str, Any]:
    runner = shlex.split(os.environ.get("V11_MANIM_BIN", "uv run manim"))
    try:
        result = subprocess.run([*runner, "--version"], capture_output=True, text=True,
                                timeout=20, check=True)
        output = (result.stdout + "\n" + result.stderr).strip()
        version = next((line.strip() for line in output.splitlines()
                        if "Manim Community v" in line or line.strip().startswith("Manim version")),
                       output.splitlines()[0] if output else "version output unavailable")
        return {"status": "PASS", "command": runner, "version": version}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "BLOCKED", "reason": f"Manim process check failed: {exc}"}


def _probe_blender(model_path: Path | None = None) -> dict[str, Any]:
    from core.mechanism.renderer import _blender_binary
    if model_path is not None and not Path(model_path).is_file():
        return {"status": "BLOCKED", "reason": f"H1 model file is missing: {model_path}"}
    try:
        executable = _blender_binary()
        result = subprocess.run([executable, "--version"], capture_output=True, text=True,
                                timeout=20, check=True)
        version = result.stdout.strip().splitlines()[0]
        return {"status": "PASS", "executable": executable, "version": version,
                "model_path": str(model_path) if model_path else None}
    except (OSError, subprocess.SubprocessError, FileNotFoundError) as exc:
        detail = getattr(exc, "stderr", None) or getattr(exc, "stdout", None)
        detail = detail.strip() if isinstance(detail, str) and detail.strip() else str(exc)
        return {"status": "BLOCKED", "reason": f"Blender process check failed: {detail}"}


def _probe_threejs(trace: dict[str, Any]) -> dict[str, Any]:
    try:
        from pilots.v10_rag_poc.build_video import has_vectors, threejs_runtime_info
        if not has_vectors(trace):
            return {"status": "BLOCKED", "reason": "trace has no recorded query/chunk vectors"}
        runtime = threejs_runtime_info()
        if runtime["status"] != "PASS":
            return runtime
        return {**runtime, "reason": "trace vectors and local browser/loopback capture runtime available"}
    except (ImportError, OSError, RuntimeError) as exc:
        return {"status": "BLOCKED", "reason": f"Three.js preflight failed: {exc}"}


def preflight(renderer_id: str, *, trace: dict[str, Any] | None = None,
              model_path: Path | None = None) -> dict[str, Any]:
    if renderer_id in {"manim", "manim_yolo_image_space"}:
        result = _probe_manim()
        if renderer_id == "manim_yolo_image_space" and trace is not None:
            image = Path(trace.get("input_image", {}).get("path", ""))
            if not image.is_file():
                return {"status": "BLOCKED", "reason": f"YOLO input image is unavailable: {image}"}
        return result
    if renderer_id == "blender_h1_trace_playback":
        return _probe_blender(model_path)
    if renderer_id == "manim+threejs":
        manim = _probe_manim()
        three = _probe_threejs(trace or {})
        return {"status": "PASS" if manim["status"] == three["status"] == "PASS" else "BLOCKED",
                "manim": manim, "threejs": three}
    return {"status": "BLOCKED", "reason": f"unknown renderer: {renderer_id}"}


def decide_renderer(*, topic: str, requested_renderer: str, visual_goal: str,
                    trace: dict[str, Any], model_path: Path | None = None,
                    preflight_result: dict[str, Any] | None = None) -> dict[str, Any]:
    if visual_goal not in VISUAL_GOALS:
        raise ValueError(f"visual_goal must be one of {', '.join(VISUAL_GOALS)}")
    if requested_renderer not in {"auto", "manim", "blender"}:
        raise ValueError("requested renderer must be auto, manim, or blender")
    resolved_goal = infer_visual_goal(topic, trace) if visual_goal == "auto" else visual_goal
    rejected: list[dict[str, str]] = []

    if topic == "object_detection":
        selected = "manim_yolo_image_space"
        reason = "actual image-space boxes and detector decisions are the required evidence"
        if requested_renderer == "blender":
            raise ValueError("Blender is not a supported renderer for object_detection")
    elif topic == "robot_kinematics":
        wants_3d = resolved_goal in {"motion_3d", "spatial_relationship"}
        if requested_renderer == "blender" and not wants_3d:
            raise ValueError(f"Blender does not fit visual goal {resolved_goal}; use Manim or change --visual-goal")
        if requested_renderer == "manim":
            if wants_3d:
                raise ValueError(f"visual goal {resolved_goal} requires the H1 3D mesh renderer")
            selected = "manim"
            reason = "the goal is analytical/comparative and is better shown with trace plots"
        elif wants_3d:
            selected = "blender_h1_trace_playback"
            reason = "the explanation requires the existing H1 mesh and spatial joint motion"
        else:
            selected = "manim"
            reason = "the inferred goal is numerical/comparative rather than spatial motion"
    elif topic == "rag":
        if requested_renderer == "blender":
            raise ValueError("Blender is not a supported renderer for RAG")
        if resolved_goal == "spatial_relationship" and requested_renderer == "auto":
            probe = preflight_result or _probe_threejs(trace)
            if probe.get("status") == "PASS":
                selected = "manim+threejs"
                reason = "recorded embedding vectors and the local 3D projection runtime support the spatial goal"
            else:
                selected = "manim"
                reason = "Three.js spatial view is unavailable; retained trace-ranked Manim explanation"
                rejected.append({"renderer": "manim+threejs", "reason": probe.get("reason", "runtime unavailable")})
        else:
            selected = "manim"
            reason = "the goal is retrieval logic or an explicit 2D renderer was requested"
    else:
        if requested_renderer == "blender":
            raise ValueError(f"Blender is not supported for topic {topic}")
        selected = "manim"
        reason = "the topic's supported evidence is numerical or algorithmic"

    if requested_renderer == "manim" and topic != "robot_kinematics":
        selected = "manim_yolo_image_space" if topic == "object_detection" else "manim"
    fallback_from_three = topic == "rag" and selected == "manim" and bool(rejected) and requested_renderer == "auto"
    candidate_preflight = (preflight("manim", trace=trace) if fallback_from_three else
                           preflight_result or preflight(selected, trace=trace, model_path=model_path))
    if fallback_from_three:
        feature_loss = ["3D embedding projection; retained trace-ranked Manim view"]
    if candidate_preflight.get("status") != "PASS":
        # Auto mode may use an explicitly recorded 2D fallback except when 3D is essential.
        if requested_renderer == "auto" and selected == "blender_h1_trace_playback" and resolved_goal == "spatial_relationship":
            rejected.append({"renderer": selected, "reason": candidate_preflight.get("reason", "runtime unavailable")})
            selected = "manim"
            reason = "3D spatial rendering unavailable; using Manim with stated 3D feature loss"
            candidate_preflight = preflight("manim", trace=trace)
            feature_loss = ["3D mesh and spatial joint-motion evidence"]
        else:
            feature_loss = (["3D embedding projection; retained trace-ranked Manim view"]
                            if selected == "manim+threejs" and requested_renderer == "auto" else [])
            if resolved_goal == "motion_3d":
                selected = None
        if selected is None or candidate_preflight.get("status") != "PASS":
            status = "BLOCKED"
        else:
            status = "PASS"
    else:
        if not fallback_from_three:
            feature_loss = []
        status = "PASS"

    return {"status": status, "requested_renderer": requested_renderer,
            "visual_goal": resolved_goal, "selected_renderer": selected,
            "selection_reason": reason, "capabilities": CAPABILITIES.get(selected, {}),
            "runtime_preflight": candidate_preflight, "rejected_candidates": rejected,
            "feature_loss": feature_loss,
            "motion_evidence": analyze_joint_motion(trace) if topic == "robot_kinematics" and (trace or {}).get("samples") else None}
