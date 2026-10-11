"""Render the registered CC0 20T:40T gear asset on the shared lesson timeline.

The imported polygonal gears are parented to temporary axis pivots. The asset
file itself is never saved or rewritten by this renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
BLENDER_KIT = REPO_ROOT / "core/blender-robotics-simulation-skill/templates"
if str(BLENDER_KIT) not in sys.path:
    sys.path.insert(0, str(BLENDER_KIT))

import bpy
from mathutils import Matrix, Vector

from core.education.gear_kinematics import external_spur_gear_kinematics
from core.education.gear_animation import plan_gear_rotation_keys
from core.education.renderer_registry import resolve_asset
from studio_utils import set_interpolation

ASSET_ID = "edu.spur_gears_20_40.v1"
OBJECTS = ("Pinion_20T", "Gear_40T", "Pinion_Hub", "Gear_Hub")
PIVOT_TOLERANCE_M = 0.001


def parse_args() -> argparse.Namespace:
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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def world_bounds(obj) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high


def bounds_center(obj) -> Vector:
    low, high = world_bounds(obj)
    return (low + high) / 2


def mesh_centroid_world(obj) -> Vector:
    if not getattr(obj.data, "vertices", None):
        raise RuntimeError(f"{obj.name} has no mesh vertices for center validation")
    total = Vector((0.0, 0.0, 0.0))
    for vertex in obj.data.vertices:
        total += obj.matrix_world @ vertex.co
    return total / len(obj.data.vertices)


def add_axis_pivot(obj, name: str, center: tuple[float, float, float]):
    """Parent while preserving world geometry; rotate the assembly at its true axis."""
    world_before = obj.matrix_world.copy()
    pivot = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.location = center
    pivot.rotation_mode = "XYZ"
    obj.parent = pivot
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = world_before
    return pivot


def validate_and_pivot(asset: dict, context: dict) -> tuple[dict, dict]:
    missing = [name for name in OBJECTS if bpy.data.objects.get(name) is None]
    if missing:
        raise RuntimeError("registered gear asset is missing objects: " + ", ".join(missing))
    results = context.get("calculated_results") or {}
    if results.get("source_asset_id") != ASSET_ID:
        raise RuntimeError("renderer context does not describe the registered gear asset")
    expected = {
        "Pinion_20T": Vector(results["pinion_center_m"]),
        "Gear_40T": Vector(results["gear_center_m"]),
    }
    geometry_report = {}
    for name, center in ("Pinion_20T", expected["Pinion_20T"]), ("Gear_40T", expected["Gear_40T"]):
        obj = bpy.data.objects[name]
        # The authored asset contains a preview action for its generator render.
        # Clear it in memory so it cannot combine with the pivot animation.
        obj.animation_data_clear()
        bpy.context.view_layer.update()
        observed = bounds_center(obj)
        error = (observed - center).length
        if error > PIVOT_TOLERANCE_M:
            raise RuntimeError(f"{name} mesh bounds center {tuple(observed)} differs from expected "
                               f"{tuple(center)} by {error:.6f} m")
        geometry_report[name] = {
            "object_origin_world_m": list(obj.matrix_world.translation),
            "mesh_bounds_center_world_m": list(observed),
            "expected_axis_center_world_m": list(center),
            "bounds_center_error_m": error,
            "bounds_world_m": [list(world_bounds(obj)[0]), list(world_bounds(obj)[1])],
        }
    for name, center in (("Pinion_Hub", expected["Pinion_20T"]),
                         ("Gear_Hub", expected["Gear_40T"])):
        obj = bpy.data.objects[name]
        observed = bounds_center(obj)
        error_xy = (Vector((observed.x, observed.y)) - Vector((center.x, center.y))).length
        if error_xy > PIVOT_TOLERANCE_M:
            raise RuntimeError(f"{name} hub axis differs from its gear center by {error_xy:.6f} m")
        geometry_report[name] = {
            "object_origin_world_m": list(obj.matrix_world.translation),
            "mesh_bounds_center_world_m": list(observed),
            "expected_axis_center_xy_m": [center.x, center.y],
            "axis_center_error_xy_m": error_xy,
            "bounds_world_m": [list(world_bounds(obj)[0]), list(world_bounds(obj)[1])],
        }

    pinion_center = tuple(expected["Pinion_20T"])
    gear_center = tuple(expected["Gear_40T"])
    pivots = {
        "Pinion_20T": add_axis_pivot(bpy.data.objects["Pinion_20T"], "V14_1_Pinion_Axis", pinion_center),
        "Pinion_Hub": add_axis_pivot(bpy.data.objects["Pinion_Hub"], "V14_1_Pinion_Axis_Hub", pinion_center),
        "Gear_40T": add_axis_pivot(bpy.data.objects["Gear_40T"], "V14_1_Gear_Axis", gear_center),
        "Gear_Hub": add_axis_pivot(bpy.data.objects["Gear_Hub"], "V14_1_Gear_Axis_Hub", gear_center),
    }
    center_distance = (expected["Gear_40T"] - expected["Pinion_20T"]).length
    if abs(center_distance - float(results["center_distance_m"])) > 1e-9:
        raise RuntimeError("asset gear centers do not match the shared kinematics center distance")
    geometry_report["center_distance_m"] = center_distance
    return pivots, geometry_report


def key_rotation(pivot, frames: list[int], angles: list[float]) -> None:
    for frame, angle in zip(frames, angles, strict=True):
        pivot.rotation_euler.z = angle
        pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)
    set_interpolation(pivot, "LINEAR", paths=["rotation_euler"])


def setup_camera_and_lights(scene, width: int, height: int, fps: int, samples: int) -> None:
    scene.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.app, "version") and bpy.app.version >= (4, 2, 0) else "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.fps, scene.render.fps_base = fps, 1.0
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = samples
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world.color = (.012, .02, .035)

    bpy.ops.object.camera_add(location=(0.14, -0.20, 0.17))
    camera = bpy.context.object
    camera.name = "V14_1_Gear_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = .138
    camera.data.clip_start = .01
    direction = Vector((.01, 0, 0)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    def area(name, location, energy, size, color):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (Vector((0, 0, 0)) - light.location).to_track_quat("-Z", "Y").to_euler()

    area("V14_1_Key_Softbox", (-.055, -.075, .11), 35, .11, (0.78, .87, 1.0))
    area("V14_1_Fill_Softbox", (.08, .04, .07), 18, .14, (1.0, .78, .48))


def add_camera_text(camera, body: str, name: str, location: tuple[float, float, float],
                    size: float, color: tuple[float, float, float, float]):
    data = bpy.data.curves.new(name + "_font", "FONT")
    data.body = body
    data.size = size
    data.align_x = "LEFT"
    data.extrude = 0
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = camera
    obj.location = location
    material = bpy.data.materials.new(name + "_emission")
    material.diffuse_color = color
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = color
    output = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    data.materials.append(material)
    return obj


def setup_labels(camera, results: dict, fps: int, phase_frames: dict[str, tuple[int, int]]) -> None:
    labels = [
        add_camera_text(camera, "INPUT  20T", "V14_1_Input_Label", (-.068, .032, -.1), .006, (.98, .68, .2, 1)),
        add_camera_text(camera, "OUTPUT  40T", "V14_1_Output_Label", (.012, -.025, -.1), .006, (.72, .86, 1, 1)),
        add_camera_text(camera, "EXTERNAL GEAR | IDEAL RATIO  -0.5", "V14_1_Ratio_Label",
                        (-.068, -.035, -.1), .0045, (.95, .97, 1, 1)),
    ]
    # Labels persist throughout the Blender track; the shared timeline decides
    # which renderer's frames are actually used for each beat.
    for label in labels:
        label.hide_render = False


def create_load_report(asset: dict, geometry: dict, pivots: dict, version: str,
                       fixed_center_validation: dict) -> dict:
    return {
        "schema": "education-asset-load-report/v1",
        "status": "PASS",
        "asset_id": ASSET_ID,
        "asset_path": asset["path"],
        "asset_sha256": asset["sha256"],
        "asset_metadata_sha256": asset["metadata_sha256"],
        "blender_loaded_objects": list(OBJECTS),
        "loaded_objects_present": True,
        "object_origins_and_mesh_centers": {key: geometry[key] for key in OBJECTS},
        "pivot_validation": "PASS",
        "axis_pivots": {name: list(pivot.matrix_world.translation) for name, pivot in pivots.items()},
        "gear_center_distance_m": geometry["center_distance_m"],
        "centers_fixed_during_animation": fixed_center_validation["status"] == "PASS",
        "fixed_center_validation": fixed_center_validation,
        "blender_version": version,
        "source_asset_modified": False,
        "limitations": ["stylized polygonal teeth are non-involute",
                        "no contact force, friction, stress, or deformation solver is run"],
    }


def render_lesson(args: argparse.Namespace) -> None:
    manifest = read_json(args.manifest)
    timeline = read_json(args.timeline)
    context = read_json(args.context)
    contract = context.get("asset_validation") or {}
    asset = resolve_asset(ASSET_ID, root=REPO_ROOT)
    if contract.get("sha256") != asset["sha256"]:
        raise RuntimeError("renderer context asset hash differs from the current registered asset")
    results = context.get("calculated_results") or {}
    expected = external_spur_gear_kinematics(
        int(results["pinion_teeth"]), int(results["gear_teeth"]), float(results["module_m"]), 1.0)
    if not math.isclose(float(results["omega_2_over_omega_1"]),
                        expected["gear_angular_velocity_rad_s"], rel_tol=0, abs_tol=1e-12):
        raise RuntimeError("renderer context ratio differs from shared ideal gear kinematics")

    # Loading the registered asset is intentional. No save operation is made.
    bpy.ops.wm.open_mainfile(filepath=str((REPO_ROOT / asset["path"]).resolve()))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    pivots, geometry = validate_and_pivot(asset, context)

    fps = int(timeline["fps"])
    if fps != args.fps:
        raise RuntimeError(f"requested fps {args.fps} does not match timeline fps {fps}")
    scene.frame_start = 1
    scene.frame_end = int(timeline["total_frames"])
    phase_frames = {row["phase_id"]: (int(row["presentation_start_frame"]) + 1,
                                     int(row["presentation_end_frame"]))
                    for row in timeline["phases"]}
    beat_by_phase = {beat["phase_id"]: beat for beat in manifest["beats"]}
    if set(phase_frames) != set(beat_by_phase):
        raise RuntimeError("manifest beats and timeline phases differ")
    ratio = float(results["omega_2_over_omega_1"])
    rotation_keys = plan_gear_rotation_keys(manifest, timeline, ratio)
    for object_name, values in rotation_keys.items():
        if values:
            key_rotation(pivots[object_name], [int(item["frame"]) for item in values],
                         [float(item["angle_rad"]) for item in values])
    sample_frames = {1, int(timeline["total_frames"])}
    for values in rotation_keys.values():
        for row in values:
            frame = int(row["frame"])
            sample_frames.update((frame, max(1, frame - 1), frame + 1))
    max_center_error = 0.0
    for frame in sorted(sample_frames):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for object_name, center in (("Pinion_20T", Vector(results["pinion_center_m"])),
                                    ("Gear_40T", Vector(results["gear_center_m"]))):
            error = (mesh_centroid_world(bpy.data.objects[object_name]) - center).length
            max_center_error = max(max_center_error, error)
            if error > PIVOT_TOLERANCE_M:
                raise RuntimeError(f"{object_name} moved off its axis by {error:.6f} m at frame {frame}")
    fixed_center_validation = {
        "status": "PASS", "sampled_frames": sorted(sample_frames),
        "max_mesh_centroid_error_m": max_center_error,
        "tolerance_m": PIVOT_TOLERANCE_M,
    }
    scene.frame_set(1)
    bpy.context.view_layer.update()

    setup_camera_and_lights(scene, args.width, args.height, args.fps, args.samples)
    setup_labels(scene.camera, results, fps, phase_frames)
    scene.render.filepath = str(args.output.resolve())
    scene.render.image_settings.file_format = "FFMPEG"
    report = create_load_report(asset, geometry, pivots, bpy.app.version_string, fixed_center_validation)
    report_path = args.output.with_name("asset_load_report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.still_frame is not None:
        scene.frame_set(max(1, min(args.still_frame, scene.frame_end)))
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(args.output.with_suffix(".png"))
        bpy.ops.render.render(write_still=True)
        return
    scene.frame_set(1)
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    render_lesson(parse_args())
