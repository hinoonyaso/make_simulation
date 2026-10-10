"""Blender-side renderer for the validated MuJoCo H1 trace payload."""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
KIT_TEMPLATES = ROOT / "core/blender-robotics-simulation-skill/templates"
sys.path.insert(0, str(KIT_TEMPLATES))
import studio_utils  # noqa: E402


def args_after_dashdash():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--font", type=Path, default=None)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    return parser.parse_args(argv)


def mat_principled(name, color, roughness=.42, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return material


def mat_emission(name, color, strength=1.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1.0)
    emission.inputs["Strength"].default_value = strength
    material.node_tree.links.new(emission.outputs["Emission"], out.inputs["Surface"])
    return material


def add_text(name, body, size, location, material, font=None, parent=None):
    data = bpy.data.curves.new(name, "FONT")
    data.body = body
    data.size = size
    data.extrude = 0
    if font:
        data.font = font
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    if parent:
        obj.parent = parent
    obj.data.materials.append(material)
    return obj


def add_line(name, points, material, bevel=.004, parent=None):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = bevel
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    if parent:
        obj.parent = parent
    obj.data.materials.append(material)
    return obj


def camera_look(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def body_material(body, mats):
    lower = body.lower()
    if any(part in lower for part in ("left_shoulder", "left_elbow", "left_hand")):
        return mats["arm"]
    if any(part in lower for part in ("hip_yaw", "hip_roll", "knee", "ankle", "thumb", "index", "middle", "ring", "pinky")):
        return mats["joint"]
    return mats["shell"]


def main():
    args = args_after_dashdash()
    payload_path = args.payload.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "h1-blender-trace-payload/v1":
        raise RuntimeError("unsupported Blender trace payload")
    expected_mapping = {"source": "MuJoCo right-handed world frame, Z-up, meters",
                       "target": "Blender right-handed world frame, Z-up, meters",
                       "transform": "identity; positions and rotations copied after FK"}
    if payload.get("coordinate_mapping") != expected_mapping:
        raise RuntimeError("MuJoCo-to-Blender frame/unit mapping is missing or unsupported")
    if args.fps != payload["fps"]:
        raise RuntimeError("render fps must match exported trace payload fps")

    studio_utils.setup_studio(profile="FINAL", frames=len(payload["frames"]))
    scene = bpy.context.scene
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    scene.frame_start = 1
    scene.frame_end = len(payload["frames"])
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 48
    scene.render.use_motion_blur = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene.render.image_settings.color_mode = "RGB"

    mats = {
        "shell": mat_principled("H1 | ceramic alloy", (.42, .47, .53), .36, .2),
        "arm": mat_principled("H1 | actuated left arm", (.015, .19, .47), .32, .18),
        "joint": mat_principled("H1 | dark joint elastomer", (.055, .075, .095), .52, .04),
    }
    ink = mat_emission("Overlay ink", (.018, .027, .04))
    muted = mat_emission("Overlay muted", (.075, .09, .11))
    target_mat = mat_emission("Target amber", (.88, .39, .045), 1.2)
    actual_mat = mat_emission("Actual blue", (.015, .32, .72), 1.2)
    white = mat_emission("Overlay white", (.98, .99, 1.0))

    # Import each compiled MuJoCo mesh once. Per-geom transforms stay sourced from the trace.
    mesh_objects = {}
    stl_root = payload_path.parent
    geoms = payload["visual_geoms"]
    for spec in geoms:
        if "mesh" not in spec or spec["mesh_id"] in mesh_objects:
            continue
        before = set(bpy.data.objects)
        stl_path = stl_root / spec["mesh"]
        bpy.ops.wm.stl_import(filepath=str(stl_path), global_scale=1.0)
        imported = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
        if not imported:
            raise RuntimeError(f"STL import produced no mesh: {stl_path}")
        obj = imported[0]
        obj.name = f"MuJoCo mesh {spec['mesh_id']}"
        obj.data.name = f"MuJoCo mesh data {spec['mesh_id']}"
        for poly in obj.data.polygons:
            poly.use_smooth = True
        mesh_objects[spec["mesh_id"]] = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)

    render_objects = {}
    for spec in geoms:
        if "mesh" in spec:
            mesh_data = mesh_objects[spec["mesh_id"]]
            obj = bpy.data.objects.new(f"H1 | {spec['body']} | geom {spec['id']}", mesh_data)
            bpy.context.collection.objects.link(obj)
        else:
            size = spec["size"]
            bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=size[0], depth=2 * size[1])
            obj = bpy.context.object
            obj.name = f"H1 | {spec['body']} | geom {spec['id']}"
        obj.data.materials.clear()
        obj.data.materials.append(body_material(spec["body"], mats))
        render_objects[spec["id"]] = obj

    lower = Vector(payload["bounds"]["min"])
    upper = Vector(payload["bounds"]["max"])
    center = (lower + upper) * .5
    floor_z = lower.z
    floor = studio_utils.add_studio_floor(size=20)
    floor.location.z = floor_z
    floor.name = "Render-only studio floor (not in MuJoCo model)"

    # Camera points from the robot's forward/right side and leaves a separate graph region.
    camera_data = bpy.data.cameras.new("H1 Trace Camera")
    camera = bpy.data.objects.new("H1 Trace Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    target = (Vector((0, 0, center.z)))
    camera.location = (2.5, -6.5, center.z + .75)
    camera_look(camera, target)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 4.45
    scene.camera = camera
    right = camera.rotation_euler.to_matrix() @ Vector((1, 0, 0))
    robot_offset = right * -.92

    # Reuse the studio helper and target its lights at the H1 bounds center.
    studio_utils.add_area_light("Key softbox", (-1.5, 2.5, 5.5), 700, 3.5, target=center)
    studio_utils.add_area_light("Fill softbox", (3.0, -3.5, 4.0), 220, 6.0, target=center)
    studio_utils.add_area_light("Rim softbox", (4.0, 3.0, 2.0), 400, 2.5, target=center)

    # Screen-space text and graph are parented to the camera for stable framing.
    font = None
    if args.font and args.font.exists():
        try:
            font = bpy.data.fonts.load(str(args.font))
        except RuntimeError:
            font = None
    title = add_text("Title", "Unitree H1 | 물리 실행 trace", .12, (.20, 1.04, -2.0), ink, font, camera)
    subtitle = add_text("Subtitle", "MuJoCo 관절 상태를 Blender 3D 메시와 그래프에 동기화", .064,
                        (.20, .86, -2.0), muted, font, camera)
    scope_copy = (f"MuJoCo {payload.get('source_duration_sec', payload['end_time']-payload['start_time']):.2f}s"
                  f" · 영상 {payload.get('presentation_duration_sec', payload['end_time']-payload['start_time']):.2f}s"
                  " · 고정 골반 / PD 토크")
    scope = add_text("Scope", scope_copy, .052, (.20, .73, -2.0), muted, font, camera)
    for phase in payload.get("phase_playback", []):
        phase_frames = [f['frame'] for f in payload['frames'] if f['phase_id'] == phase['phase_id']]
        speed = phase['playback_speed']
        label = ("정지 · 분석" if phase['playback_state'] == 'hold' else
                 "배속 미정" if speed is None else f"운동 구간 재생 {speed:.2f}×")
        obj = add_text("Playback_" + phase['phase_id'], label, .06, (.20, -.80, -2.0), ink, font, camera)
        # Visibility drivers persist in the saved .blend and switch on exact video frame boundaries.
        for prop in ('hide_render', 'hide_viewport'):
            obj.driver_add(prop).driver.expression = f"frame < {min(phase_frames)} or frame > {max(phase_frames)}"

    # Graph of actual and commanded left-shoulder angles from the same trace.
    gx0, gx1 = .20, 1.91
    gy0, gy1 = -.53, .39
    target_values = np.asarray([frame["target"][0] for frame in payload["frames"]], dtype=float)
    actual_values = np.asarray([frame["qpos"][payload["shoulder_index"]] for frame in payload["frames"]], dtype=float)
    ymin = min(float(target_values.min()), float(actual_values.min())) - .04
    ymax = max(float(target_values.max()), float(actual_values.max())) + .04
    def graph_x(source_time):
        duration = payload["end_time"] - payload["start_time"]
        ratio = 0.0 if duration <= 0 else (float(source_time) - payload["start_time"]) / duration
        return gx0 + (gx1 - gx0) * ratio
    def graph_y(value):
        return gy0 + (gy1 - gy0) * (value - ymin) / (ymax - ymin)
    add_text("Graph title", "왼쪽 어깨 각도 (rad)", .068, (gx0, .57, -2.0), ink, font, camera)
    add_text("Graph legend target", "목표", .05, (gx0, .47, -2.0), target_mat, font, camera)
    add_text("Graph legend actual", "실제", .05, (gx0 + .34, .47, -2.0), actual_mat, font, camera)
    grid = mat_emission("Graph grid", (.58, .62, .66))
    for k in range(4):
        y = gy0 + (gy1 - gy0) * k / 3
        add_line(f"Graph grid {k}", [(gx0, y, -2.01), (gx1, y, -2.01)], grid, .0015, camera)
    add_line("Graph axis x", [(gx0, gy0, -2.01), (gx1, gy0, -2.01)], muted, .002, camera)
    source_values = [float(frame["source_time_sec"]) for frame in payload["frames"]]
    add_line("Target angle", [(graph_x(t), graph_y(v), -2.0)
                              for t, v in zip(source_values, target_values)], target_mat, .006, camera)
    add_line("Actual angle", [(graph_x(t), graph_y(v), -2.0)
                              for t, v in zip(source_values, actual_values)], actual_mat, .006, camera)
    add_text("Y max", f"{ymax:.2f}", .042, (gx1 + .025, gy1 - .015, -2.0), muted, font, camera)
    add_text("Y min", f"{ymin:.2f}", .042, (gx1 + .025, gy0 - .015, -2.0), muted, font, camera)
    add_text("X zero", f"{payload['start_time']:.1f} s", .042, (gx0, gy0 - .10, -2.0), muted, font, camera)
    add_text("X end", f"{payload['end_time']:.1f} s", .042, (gx1 - .2, gy0 - .10, -2.0), muted, font, camera)
    cursor = add_line("Graph time cursor", [(gx0, gy0 - .015, -2.02), (gx0, gy1 + .015, -2.02)], white, .003, camera)
    cursor.data.splines[0].points[0].keyframe_insert(data_path="co", frame=1)
    cursor.data.splines[0].points[1].keyframe_insert(data_path="co", frame=1)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=.025, location=(0, 0, 0))
    actual_dot = bpy.context.object
    actual_dot.name = "Graph actual marker"
    actual_dot.parent = camera
    actual_dot.data.materials.append(actual_mat)
    target_dot = actual_dot.copy(); target_dot.data = actual_dot.data.copy()
    bpy.context.collection.objects.link(target_dot)
    target_dot.name = "Graph target marker"
    target_dot.data.materials.clear(); target_dot.data.materials.append(target_mat)

    hand_path_points = []
    for pos in payload["hand_path"]:
        v = Vector(pos) + robot_offset
        hand_path_points.append(tuple(v))
    trajectory_mat = mat_emission("Hand path", (.01, .38, .67), .85)
    path_obj = add_line("Recorded hand trajectory", hand_path_points, trajectory_mat, .003)
    # Static reference path; do not animate apparent motion during timeline holds.
    path_obj.data.bevel_factor_end = 1.0
    for action in bpy.data.actions:
        for curve in getattr(action, "fcurves", []):
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"

    for idx, frame in enumerate(payload["frames"]):
        frame_number = frame["frame"]
        by_id = {item["id"]: item for item in frame["transforms"]}
        for geom_id, obj in render_objects.items():
            transform = by_id[geom_id]
            pos = Vector(transform["position"]) + robot_offset
            rot = Matrix((transform["rotation"][0:3], transform["rotation"][3:6], transform["rotation"][6:9]))
            obj.location = pos
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = rot.to_quaternion()
            obj.keyframe_insert(data_path="location", frame=frame_number)
            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame_number)
        cursor_pts = cursor.data.splines[0].points
        source_time = frame["source_time_sec"]
        for point, co in zip(cursor_pts, ((graph_x(source_time), gy0 - .015, -2.02),
                                          (graph_x(source_time), gy1 + .015, -2.02))):
            point.co = (*co, 1)
            point.keyframe_insert(data_path="co", frame=frame_number)
        actual_dot.location = (graph_x(source_time), graph_y(float(actual_values[idx])), -2.03)
        target_dot.location = (graph_x(source_time), graph_y(float(target_values[idx])), -2.03)
        actual_dot.keyframe_insert(data_path="location", frame=frame_number)
        target_dot.keyframe_insert(data_path="location", frame=frame_number)

    scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.use_file_extension = True
    scene.render.filepath = str(out / "h1_trace_blender.mp4")
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.frame_set(1)
    blend_path = out / "h1_trace_blender.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.render.render(animation=True)
    print("RENDERED_MP4", scene.render.filepath)
    print("TRACE_SHA256", payload["trace_sha256"])
    print("BLENDER_VERSION", bpy.app.version_string)


if __name__ == "__main__":
    # numpy is present in Blender's bundled Python; avoid loading any project package in Blender.
    import numpy as np
    main()
