"""Fixed-base MuJoCo arm experiment, recorder, and robotics-visual-trace projection."""
from __future__ import annotations

import hashlib
import json
import math
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

SCHEMA = "robotics-visual-trace/v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _compile_fixed_base(model_path: Path, timestep: float):
    tree = ET.parse(model_path)
    root = tree.getroot()
    compiler = root.find("compiler")
    if compiler is None:
        compiler = ET.SubElement(root, "compiler")
    relative_meshdir = compiler.get("meshdir", "")
    meshdir = (model_path.parent / relative_meshdir).resolve()
    compiler.set("meshdir", str(meshdir))
    pelvis = root.find("./worldbody/body[@name='pelvis']")
    if pelvis is None or pelvis.find("freejoint") is None:
        raise ValueError("expected H1 pelvis body with a freejoint")
    pelvis.remove(pelvis.find("freejoint"))
    option = root.find("option")
    if option is None:
        option = ET.SubElement(root, "option")
    option.set("timestep", str(timestep))
    with tempfile.TemporaryDirectory(prefix="mujoco-fixed-h1-") as tmp:
        temp_xml = Path(tmp) / "h1_fixed.xml"
        tree.write(temp_xml, encoding="utf-8", xml_declaration=True)
        yield_model = mujoco.MjModel.from_xml_path(str(temp_xml))
    return yield_model


def _target(t: float, duration: float) -> tuple[float, float]:
    """Smooth raise/hold/lower trajectory for left shoulder and elbow, radians."""
    phase = t / duration
    if phase < 0.35:
        u = phase / 0.35
    elif phase < 0.68:
        u = 1.0
    else:
        u = max(0.0, (1.0 - phase) / 0.32)
    blend = u * u * (3.0 - 2.0 * u)
    return 0.35 * blend, 0.55 * blend


def run_arm_experiment(model_path: str | Path, output_dir: str | Path,
                       duration: float = 2.0, timestep: float = 0.002,
                       sample_period: float = 0.02) -> dict[str, Any]:
    model_path = Path(model_path).resolve()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for label, value in (("duration", duration), ("timestep", timestep),
                         ("sample_period", sample_period)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{label} must be positive and finite")
    ratio = duration / timestep
    sample_ratio = sample_period / timestep
    if not math.isclose(ratio, round(ratio), abs_tol=1e-9):
        raise ValueError("duration must be divisible by timestep")
    if not math.isclose(sample_ratio, round(sample_ratio), abs_tol=1e-9):
        raise ValueError("sample_period must be divisible by timestep")

    model = _compile_fixed_base(model_path, timestep)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    joint_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
                   for i in range(model.njnt)]
    if any(name is None for name in joint_names):
        raise ValueError("all joints must have stable names for trace recording")
    joint_ids = {name: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
                 for name in joint_names}
    actuator_joints: dict[int, str] = {}
    for actuator_id in range(model.nu):
        joint_id = int(model.actuator_trnid[actuator_id, 0])
        if joint_id < 0 or joint_id >= model.njnt:
            raise ValueError(f"actuator {actuator_id} is not directly attached to a joint")
        actuator_joints[actuator_id] = joint_names[joint_id]
    body_ids = {name: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
                for name in ("left_shoulder_pitch_link", "left_elbow_link", "left_hand_link")}
    if any(value < 0 for value in body_ids.values()):
        raise ValueError("H1 model must contain left shoulder, elbow and hand bodies")
    target_joints = {"left_shoulder_pitch_joint", "left_elbow_joint"}
    if not target_joints.issubset(joint_ids):
        raise ValueError("H1 model is missing the controlled joints")

    qpos_addr = {name: int(model.jnt_qposadr[jid]) for name, jid in joint_ids.items()}
    dof_addr = {name: int(model.jnt_dofadr[jid]) for name, jid in joint_ids.items()}
    actuator_for_joint = {joint: aid for aid, joint in actuator_joints.items()}
    if not target_joints.issubset(actuator_for_joint):
        raise ValueError("controlled joints need direct MuJoCo actuators")
    limits = model.actuator_ctrlrange.copy()

    def capture(sample_time: float) -> dict[str, Any]:
        shoulder = body_ids["left_shoulder_pitch_link"]
        elbow = body_ids["left_elbow_link"]
        hand = body_ids["left_hand_link"]
        shoulder_target, elbow_target = _target(sample_time, duration)
        return {
            "t": float(data.time),
            "qpos": data.qpos.astype(float).tolist(),
            "qvel": data.qvel.astype(float).tolist(),
            "ctrl": data.ctrl.astype(float).tolist(),
            "target": [shoulder_target, elbow_target],
            "shoulder_pos": data.xpos[shoulder].astype(float).tolist(),
            "elbow_pos": data.xpos[elbow].astype(float).tolist(),
            "ee_pos": data.xpos[hand].astype(float).tolist(),
            "ee_quat": data.xquat[hand].astype(float).tolist(),
            "ncon": int(data.ncon),
        }

    samples = [capture(0.0)]
    steps = int(round(duration / timestep))
    stride = int(round(sample_period / timestep))
    kp, kd = 35.0, 4.0
    for step in range(1, steps + 1):
        now = (step - 1) * timestep
        shoulder_target, elbow_target = _target(now, duration)
        desired = {"left_shoulder_pitch_joint": shoulder_target,
                   "left_elbow_joint": elbow_target}
        data.ctrl[:] = 0.0
        for actuator_id, joint_name in actuator_joints.items():
            reference = desired.get(joint_name, 0.0)
            error = reference - data.qpos[qpos_addr[joint_name]]
            effort = kp * error - kd * data.qvel[dof_addr[joint_name]]
            if model.actuator_ctrllimited[actuator_id]:
                effort = float(np.clip(effort, limits[actuator_id, 0], limits[actuator_id, 1]))
            data.ctrl[actuator_id] = effort
        mujoco.mj_step(model, data)
        if step % stride == 0 or step == steps:
            # mj_step may leave derived body transforms at the pre-integration state.
            mujoco.mj_forward(model, data)
            samples.append(capture(data.time))

    if not np.isfinite(np.asarray([sample["qpos"] for sample in samples])).all():
        raise RuntimeError("non-finite joint position in simulation trace")
    if not np.isfinite(np.asarray([sample["qvel"] for sample in samples])).all():
        raise RuntimeError("non-finite joint velocity in simulation trace")

    # Independent forward pass from recorded generalized coordinates validates hand pose export.
    fk_data = mujoco.MjData(model)
    max_fk_error = 0.0
    hand_id = body_ids["left_hand_link"]
    for sample in samples:
        fk_data.qpos[:] = sample["qpos"]
        mujoco.mj_forward(model, fk_data)
        error = float(np.linalg.norm(fk_data.xpos[hand_id] - sample["ee_pos"]))
        max_fk_error = max(max_fk_error, error)
    if max_fk_error > 1e-9:
        raise RuntimeError(f"recorded end-effector FK mismatch: {max_fk_error:g} m")
    endpoint_travel = float(np.linalg.norm(np.asarray(samples[-1]["ee_pos"]) -
                                           np.asarray(samples[0]["ee_pos"])))
    max_joint_limit_violation = 0.0
    for sample in samples:
        for joint_id, joint_name in enumerate(joint_names):
            if model.jnt_limited[joint_id]:
                q = sample["qpos"][qpos_addr[joint_name]]
                low, high = model.jnt_range[joint_id]
                max_joint_limit_violation = max(max_joint_limit_violation,
                                                float(max(low - q, q - high, 0.0)))
    if max_joint_limit_violation > 1e-6:
        raise RuntimeError(f"joint limit violation: {max_joint_limit_violation:g} rad")
    joint_index = {name: i for i, name in enumerate(joint_names)}
    max_tracking_error = {
        "left_shoulder_pitch_joint": max(abs(s["qpos"][joint_index["left_shoulder_pitch_joint"]] - s["target"][0]) for s in samples),
        "left_elbow_joint": max(abs(s["qpos"][joint_index["left_elbow_joint"]] - s["target"][1]) for s in samples),
    }
    peak_target = max(max(abs(s["target"][0]), abs(s["target"][1])) for s in samples)
    if peak_target <= 0 or max(np.linalg.norm(np.asarray(s["ee_pos"]) - samples[0]["ee_pos"])
                               for s in samples) < 1e-3:
        raise RuntimeError("actuation did not produce a measurable end-effector movement")

    trace = {
        "schema": SCHEMA,
        "source": "MuJoCo 3.7.0 physics run: Unitree H1 arm with fixed pelvis and PD torque control; not hardware",
        "units": {"time": "s", "qpos": "rad (fixed-base revolute joints)",
                  "qvel": "rad/s", "ctrl": "N·m motor command", "target": "rad",
                  "shoulder_pos": "m XYZ world", "elbow_pos": "m XYZ world",
                  "ee_pos": "m XYZ world", "ee_quat": "unit quaternion WXYZ",
                  "ncon": "count"},
        "fps": 30,
        "control_dt": timestep,
        "model": {"id": "unitree_h1_with_hand", "asset_id": "blender.unitree_h1.v1",
                  "source_file": str(model_path),
                  "source_sha256": sha256(model_path), "asset_license": "BSD-3-Clause",
                  "source_revision": "ccfc6fd8430a17ba3dacef9a1e2faf64ff3b0aee",
                  "engine": "MuJoCo", "engine_version": mujoco.__version__,
                  "timestep": timestep,
                  "solver": {"type": int(model.opt.solver),
                             "name": mujoco.mjtSolver(model.opt.solver).name,
                             "iterations": int(model.opt.iterations),
                             "tolerance": float(model.opt.tolerance)},
                  "gravity": model.opt.gravity.astype(float).tolist(),
                  "base_mode": "fixed pelvis; freejoint removed in temporary derived MJCF",
                  "control_mode": "closed-loop PD torque; zero targets on non-demonstrated joints",
                  "controlled_joints": sorted(target_joints),
                  "joint_names_in_qpos_order": joint_names,
                  "actuator_joint_order": [actuator_joints[i] for i in range(model.nu)],
                  "kp": kp, "kd": kd,
                  "contacts_are_lesson_evidence": False,
                  "assumptions": ["fixed pelvis", "source inertias/collision geoms retained",
                                  "gravity enabled", "no external floor/contact task",
                                  "ideal motor torque controller; no hardware claim"]},
        "validation": {"fk_max_position_error_m": max_fk_error,
                       "max_joint_limit_violation_rad": max_joint_limit_violation,
                       "end_effector_travel_m": endpoint_travel,
                       "max_contacts": max(sample["ncon"] for sample in samples),
                       "max_target_tracking_error_rad": max_tracking_error,
                       "sample_count": len(samples), "simulated_seconds": float(data.time)},
        "samples": samples,
    }
    trace_path = out / "trace.json"
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return trace
