#!/usr/bin/env python3
"""Export a validated MuJoCo H1 trace and model geometry for Blender playback."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import struct
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core/robotics-simulation"))
import mujoco_adapter  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_binary_stl(path: Path, vertices: np.ndarray, faces: np.ndarray) -> None:
    with path.open("wb") as stream:
        stream.write(b"MuJoCo compiled mesh; meters; Unitree BSD-3-Clause".ljust(80, b"\0"))
        stream.write(struct.pack("<I", len(faces)))
        for face in faces:
            tri = vertices[face]
            normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            norm = np.linalg.norm(normal)
            normal = normal / norm if norm else np.zeros(3)
            stream.write(struct.pack("<12fH", *normal, *tri[0], *tri[1], *tri[2], 0))


def _interp(samples: list[dict], t: float, key: str) -> np.ndarray:
    times = np.asarray([s["t"] for s in samples], dtype=np.float64)
    values = np.asarray([s[key] for s in samples], dtype=np.float64)
    return np.asarray([np.interp(t, times, values[:, i]) for i in range(values.shape[1])])


def export(trace_path: Path, model_path: Path, out_dir: Path, fps: int = 30) -> Path:
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    if trace.get("schema") != "robotics-visual-trace/v1":
        raise ValueError("expected robotics-visual-trace/v1")
    if trace.get("model", {}).get("engine") != "MuJoCo":
        raise ValueError("trace provenance must identify MuJoCo")
    model_hash = sha256(model_path)
    if model_hash != trace["model"].get("source_sha256"):
        raise ValueError("trace source model hash does not match the selected MJCF")
    samples = trace.get("samples", [])
    if len(samples) < 2:
        raise ValueError("trace must contain at least two samples")
    times = np.asarray([s["t"] for s in samples], dtype=np.float64)
    if not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError("trace sample timestamps must be finite and strictly increasing")

    model = mujoco_adapter._compile_fixed_base(model_path, float(trace["model"]["timestep"]))
    data = mujoco.MjData(model)
    if model.nq != len(samples[0]["qpos"]):
        raise ValueError(f"trace qpos length {len(samples[0]['qpos'])} != model nq {model.nq}")
    body_indices = {
        key: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        for key, name in (("shoulder_pos", "left_shoulder_pitch_link"),
                          ("elbow_pos", "left_elbow_link"), ("ee_pos", "left_hand_link"))
    }
    fk_error = 0.0
    for sample in samples:
        data.qpos[:] = sample["qpos"]
        mujoco.mj_forward(model, data)
        for key, body_id in body_indices.items():
            fk_error = max(fk_error, float(np.linalg.norm(data.xpos[body_id] - sample[key])))
    if fk_error > 1e-6:
        raise ValueError(f"trace body poses do not match forward kinematics: {fk_error:g} m")

    out_dir.mkdir(parents=True, exist_ok=True)
    mesh_dir = out_dir / "meshes"
    mesh_dir.mkdir(exist_ok=True)
    visual_ids = [i for i in range(model.ngeom) if int(model.geom_group[i]) in (1, 2)]
    meshes: dict[int, str] = {}
    for geom_id in visual_ids:
        if int(model.geom_type[geom_id]) != int(mujoco.mjtGeom.mjGEOM_MESH):
            continue
        mesh_id = int(model.geom_dataid[geom_id])
        if mesh_id in meshes:
            continue
        va = int(model.mesh_vertadr[mesh_id]); vn = int(model.mesh_vertnum[mesh_id])
        fa = int(model.mesh_faceadr[mesh_id]); fn = int(model.mesh_facenum[mesh_id])
        filename = f"mesh_{mesh_id:03d}.stl"
        write_binary_stl(mesh_dir / filename,
                         model.mesh_vert[va:va + vn], model.mesh_face[fa:fa + fn])
        meshes[mesh_id] = f"meshes/{filename}"

    start, end = float(times[0]), float(times[-1])
    frame_count = int(round((end - start) * fps)) + 1
    render_times = np.linspace(start, end, frame_count)
    frames = []
    bounds_min = np.full(3, np.inf); bounds_max = np.full(3, -np.inf)
    geom_specs = []
    for geom_id in visual_ids:
        body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[geom_id])) or f"body_{geom_id}"
        spec = {"id": geom_id, "body": body, "type": int(model.geom_type[geom_id]),
                "mesh_id": int(model.geom_dataid[geom_id]), "size": model.geom_size[geom_id].astype(float).tolist(),
                "rgba": model.geom_rgba[geom_id].astype(float).tolist()}
        if spec["type"] == int(mujoco.mjtGeom.mjGEOM_MESH):
            spec["mesh"] = meshes[spec["mesh_id"]]
        geom_specs.append(spec)

    mesh_bounds = {}
    for mesh_id in meshes:
        a = int(model.mesh_vertadr[mesh_id]); n = int(model.mesh_vertnum[mesh_id])
        verts = model.mesh_vert[a:a + n]
        mesh_bounds[mesh_id] = np.stack([verts.min(axis=0), verts.max(axis=0)]).tolist()

    for frame_num, t in enumerate(render_times, start=1):
        qpos = _interp(samples, float(t), "qpos")
        data.qpos[:] = qpos
        mujoco.mj_forward(model, data)
        transforms = []
        for spec in geom_specs:
            geom_id = spec["id"]
            pos = data.geom_xpos[geom_id].copy()
            rot = data.geom_xmat[geom_id].reshape(3, 3).copy()
            spec_bounds = (np.asarray(mesh_bounds[spec["mesh_id"]]) if "mesh" in spec else
                           np.stack([-np.asarray(spec["size"]), np.asarray(spec["size"])]))
            corners = np.array([[x, y, z] for x in spec_bounds[:, 0] for y in spec_bounds[:, 1] for z in spec_bounds[:, 2]])
            world_corners = corners @ rot.T + pos
            bounds_min = np.minimum(bounds_min, world_corners.min(axis=0))
            bounds_max = np.maximum(bounds_max, world_corners.max(axis=0))
            transforms.append({"id": geom_id, "position": pos.tolist(), "rotation": rot.reshape(-1).tolist()})
        frames.append({"frame": frame_num, "t": float(t), "qpos": qpos.tolist(),
                       "target": _interp(samples, float(t), "target").tolist(),
                       "transforms": transforms})

    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "left_hand_link")
    hand_path = []
    for frame in frames:
        data.qpos[:] = frame["qpos"]
        mujoco.mj_forward(model, data)
        hand_path.append(data.xpos[body_id].astype(float).tolist())
    joint_names = trace["model"]["joint_names_in_qpos_order"]
    payload = {"schema": "h1-blender-trace-payload/v1", "source_trace": str(trace_path),
               "trace_sha256": sha256(trace_path), "model_sha256": model_hash,
               "asset_license": trace["model"]["asset_license"], "engine": "MuJoCo",
               "mode": "validated trace playback; qpos linearly interpolated at render fps",
               "fps": fps, "start_time": start, "end_time": end,
               "interpolation": "linear between stored qpos samples; no new physics integration",
               "joint_names": joint_names,
               "shoulder_index": joint_names.index("left_shoulder_pitch_joint"),
               "visual_geoms": geom_specs, "frames": frames, "hand_path": hand_path,
               "bounds": {"min": bounds_min.tolist(), "max": bounds_max.tolist()}}
    payload_path = out_dir / "blender_payload.json"
    payload_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return payload_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, default=ROOT / "pilots/v10_mujoco_arm/data/trace.json")
    parser.add_argument("--model", type=Path, default=ROOT / "assets/unitree_h1/mjcf/h1_with_hand.xml")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / "core/shared-data/validate_trace.py"),
                    str(args.trace.resolve())], check=True)
    path = export(args.trace.resolve(), args.model.resolve(), args.out.resolve(), args.fps)
    print(f"PASS: trace/model provenance and {args.fps}fps render payload -> {path}")


if __name__ == "__main__":
    main()
