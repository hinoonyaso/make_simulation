"""Render the existing CC0 18650 concept asset and map validated SOC to a gauge."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BLENDER_KIT = ROOT / "core/blender-robotics-simulation-skill/templates"
if str(BLENDER_KIT) not in sys.path:
    sys.path.insert(0, str(BLENDER_KIT))
from studio_utils import set_interpolation
from core.education.blender_compat import configure_eevee
from core.education.renderer_registry import resolve_asset

ASSET_ID = "edu.mechanical_primitives.v1"
CELL_OBJECTS = ("Cell_18650_Can", "Cell_Cathode_Can", "Cell_Anode_Cap",
                "Cathode_Electrode", "Separator", "Anode_Electrode")


def args_from_blender() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--still-frame", type=int, default=None)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def world_bounds(obj) -> tuple[list[float], list[float]]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return ([min(point[i] for point in points) for i in range(3)],
            [max(point[i] for point in points) for i in range(3)])


def create_text(camera, body: str, x: float, y: float, *, size: float = .009):
    data = bpy.data.curves.new("Battery_Label", type="FONT")
    data.body = body
    data.size = size
    data.extrude = 0
    obj = bpy.data.objects.new("Battery_Label", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.rotation_euler = camera.rotation_euler
    bpy.context.view_layer.update()
    obj.location = camera.matrix_world @ Vector((x, y, -.22))
    data.materials.append(new_emission_material("Battery_Label_Material", (.78, .86, .94, 1.0), 1.0))
    return obj


def new_emission_material(name: str, color: tuple[float, float, float, float], strength: float):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength
    output = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs[0], output.inputs["Surface"])
    return material


def setup_scene(scene, camera_target: Vector, width: int, height: int, fps: int, samples: int):
    configure_eevee(scene, samples)
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.world.color = (.018, .027, .043)
    scene.frame_start = 1
    bpy.ops.object.camera_add(location=camera_target + Vector((.15, -.42, .19)))
    camera = bpy.context.object
    camera.name = "Battery_Studio_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = .205
    camera.rotation_euler = (camera_target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    bpy.ops.object.light_add(type="AREA", location=camera_target + Vector((.12, -.17, .24)))
    key = bpy.context.object
    key.name = "Battery_Key_Softbox"
    key.data.energy = 18
    key.data.shape = "DISK"
    key.data.size = .22
    key.rotation_euler = (camera_target - key.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=camera_target + Vector((-.20, .08, .10)))
    fill = bpy.context.object
    fill.name = "Battery_Fill_Softbox"
    fill.data.energy = 8
    fill.data.size = .28
    fill.rotation_euler = (camera_target - fill.location).to_track_quat("-Z", "Y").to_euler()
    return camera


def add_soc_gauge(scene, camera):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(.044, .12, 0))
    backing = bpy.context.object
    backing.name = "Solver_SOC_Gauge_Background"
    backing.dimensions = (.014, .008, .074)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    backing.data.materials.append(new_emission_material("SOC_Gauge_Dark", (.07, .11, .16, 1), 1))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(.044, .113, -.037))
    fill = bpy.context.object
    fill.name = "Solver_SOC_Gauge_Fill"
    fill.dimensions = (.010, .004, .074)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    fill.data.materials.append(new_emission_material("SOC_Gauge_Fill_Material", (.12, .66, .92, 1), 1))
    fill["base_height_m"] = .074
    create_text(camera, "18650 EDUCATION MODEL", -0.080, .052, size=.007)
    create_text(camera, "MODEL SOC", .027, .052, size=.006)
    return backing, fill


def animate_soc(fill, data: dict[str, list[float]], phase: dict, fps: int,
                initial_soc: float, max_height: float = .074):
    start = int(phase["presentation_start_frame"]) + 1
    end_exclusive = int(phase["presentation_end_frame"]) + 1
    duration_frames = end_exclusive - start
    if duration_frames <= 0:
        raise ValueError("battery SOC presentation phase is empty")
    t = np.asarray(data["time_s"], dtype=float)
    soc = np.asarray(data["estimated_soc"], dtype=float)
    result_end = float(t[-1])
    if result_end <= 0 or t[0] != 0:
        raise ValueError("solver timeseries range is invalid for SOC animation")
    for local in range(duration_frames):
        fraction = local / max(1, duration_frames - 1)
        solver_time = fraction * result_end
        value = float(np.interp(solver_time, t, soc))
        if solver_time < t[0] or solver_time > t[-1]:
            raise ValueError("presentation timeline would extrapolate beyond solver output")
        displayed = max(0.0, min(initial_soc, value)) / initial_soc
        frame = start + local
        fill.scale.z = displayed
        fill.location.z = -.037 + max_height * displayed / 2
        fill.keyframe_insert("scale", frame=frame)
        fill.keyframe_insert("location", frame=frame)
    set_interpolation(fill, "LINEAR")


def render_lesson(args: argparse.Namespace):
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
    context = json.loads(args.context.read_text(encoding="utf-8"))
    asset = resolve_asset(ASSET_ID)
    if context.get("asset_id") != ASSET_ID or context.get("asset_validation", {}).get("sha256") != asset["sha256"]:
        raise RuntimeError("battery renderer context does not match the registered CC0 cell asset")
    if context.get("solver_result", {}).get("solver_id") != "pybamm":
        raise RuntimeError("battery renderer requires a validated PyBaMM solver result")
    csv_path = args.context.parent / context["solver_result"]["timeseries_file"]
    if sha256(csv_path) != context["solver_result"].get("result_sha256"):
        raise RuntimeError("battery Blender renderer received a timeseries SHA-256 mismatch")
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    data = {key: [float(row[key]) for row in rows]
            for key in ("time_s", "terminal_voltage_v", "current_a", "discharge_capacity_ah", "estimated_soc")}
    result = json.loads((args.context.parent / context["solver_result"]["result_file"]).read_text(encoding="utf-8"))
    if result.get("result_sha256") != context["solver_result"].get("result_sha256"):
        raise RuntimeError("battery Blender renderer result manifest disagrees with the V9 context")

    source_asset = ROOT / asset["path"]
    bpy.ops.wm.open_mainfile(filepath=str(source_asset))
    missing = [name for name in asset["metadata"]["objects"] if bpy.data.objects.get(name) is None]
    if missing:
        raise RuntimeError("registered education Blender asset is missing objects: " + ", ".join(missing))
    missing_cell = [name for name in CELL_OBJECTS if bpy.data.objects.get(name) is None]
    if missing_cell:
        raise RuntimeError("registered battery geometry is missing objects: " + ", ".join(missing_cell))
    bpy.context.view_layer.update()
    bounds = {name: world_bounds(bpy.data.objects[name]) for name in CELL_OBJECTS}
    all_asset_objects = set(asset["metadata"]["objects"])
    for obj in bpy.data.objects:
        if obj.type == "MESH" or obj.type == "CURVE":
            obj.hide_render = obj.name not in CELL_OBJECTS
    scene = bpy.context.scene
    target = Vector((-.025, .12, 0))
    camera = setup_scene(scene, target, args.width, args.height, args.fps, args.samples)
    backing, fill = add_soc_gauge(scene, camera)
    phase_by_id = {phase["phase_id"]: phase for phase in timeline["phases"]}
    if "discharge_state" not in phase_by_id:
        raise RuntimeError("battery timeline has no discharge_state phase")
    animate_soc(fill, data, phase_by_id["discharge_state"], args.fps,
                float(result["initial_soc"]))
    # Keep all poses derived from the one validated model result and shared timeline.
    scene.frame_end = int(timeline["total_frames"])
    scene.render.filepath = str(args.output)
    if scene.render.filepath.lower().endswith(".mp4"):
        scene.render.filepath = scene.render.filepath[:-4]
    report = {
        "status": "PASS", "validation_contract": "battery_education_asset",
        "asset_id": ASSET_ID, "asset_sha256": asset["sha256"],
        "blender_loaded_objects": sorted(all_asset_objects), "loaded_objects_present": True,
        "battery_objects": list(CELL_OBJECTS), "geometry_validation": "PASS",
        "battery_object_bounds_m": {name: [low, high] for name, (low, high) in bounds.items()},
        "solver_id": "pybamm", "solver_run_id": context["solver_result"]["run_id"],
        "solver_result_sha256": context["solver_result"]["result_sha256"],
        "visual_mapping": "estimated_soc only; no electrode concentration, temperature, electric field, or current-density field",
        "fixed_center_validation": {"status": "NOT_APPLICABLE"},
        "blender_version": bpy.app.version_string,
        "selected_render_engine": scene.render.engine,
        "solver_actual_end_time_s": float(result["actual_end_time_s"]),
    }
    report_path = args.output.parent / "asset_load_report.json"
    scene.frame_set(1)
    if args.still_frame is not None:
        if args.still_frame < 1 or args.still_frame > scene.frame_end:
            raise ValueError(f"still frame must be between 1 and {scene.frame_end}")
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.media_type = "IMAGE"
        still_path = args.output.with_suffix(".png").resolve()
        scene.render.filepath = str(still_path)
        scene.frame_set(args.still_frame)
        bpy.ops.render.render(write_still=True)
        report["still_frame"] = args.still_frame
        report["still_output"] = str(still_path)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not still_path.is_file() or still_path.stat().st_size == 0:
            raise RuntimeError(f"Blender did not produce its expected still frame: {still_path}")
        return
    scene.render.filepath = str(args.output.resolve())
    bpy.ops.render.render(animation=True)
    encoded = args.output.with_suffix(".mp4")
    if not encoded.is_file() or encoded.stat().st_size == 0:
        raise RuntimeError(f"Blender did not produce its expected MP4: {encoded}")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    render_lesson(args_from_blender())
