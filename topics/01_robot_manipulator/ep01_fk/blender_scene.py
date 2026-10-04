"""Trace-driven Blender shots for EP01 Scenes 1 and 4.

Windows Blender 5.2 / WSL examples::

    blender.exe --background --factory-startup --python blender_scene.py -- --preview
    blender.exe --background --factory-startup --python blender_scene.py -- --render --workbench

The scene uses the shared scene kit, preserves the analytic yaw/pitch/pitch chain,
and writes a deduplicated PNG sequence plus a 5,351-entry frame map.  Frames
outside the two assigned Blender scenes are represented by null entries.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
KIT = PROJECT / "core" / "blender-robotics-simulation-skill" / "templates"
sys.path.insert(0, str(KIT))

# Required shared construction kit.  Local helpers below only add topic geometry.
import scene_kit as shared_scene_kit  # noqa: E402
from scene_kit import (  # noqa: E402
    add_coordinate_frame,
    add_cube,
    add_cylinder,
    add_point,
    assign_material,
    bootstrap,
    curve_between,
    look_at,
    principled_material,
)


OUT = ROOT / "output" / "blender"
FRAMES = OUT / "frames"
TRACE_PATH = ROOT / "output" / "trace.json"
TIMELINE_PATH = ROOT / "output" / "timeline.json"
BLEND_PATH = OUT / "ep01_fk_scenes_1_4.blend"
FPS = 30
L1, L2, H = 2.0, 1.5, 0.6
VIEWPORT = (1080, 720)
BLENDER_SCENES = {1, 4}

HEX = {
    "bg": "#F7F9FC",
    "floor": "#EDF1F6",
    "dark": "#243247",
    "inactive": "#8B95A1",
    "link1": "#7867C5",
    "link2": "#AAB2BD",
    "amber": "#E6A027",
    "x": "#E74C3C",
    "y": "#2ECC71",
    "z": "#3498DB",
    "plane": "#D8E0EA",
    "ghost": "#CBD2DC",
}

MATS: dict[str, bpy.types.Material] = {}
GROUPS: dict[str, list[bpy.types.Object]] = {}


def srgb_linear(value: str) -> tuple[float, float, float, float]:
    rgb = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return (*linear, 1.0)


def make_material(name: str, hex_value: str, roughness: float = 0.48, metallic: float = 0.0):
    rgba = srgb_linear(hex_value)
    mat = principled_material(name, rgba, roughness=roughness, metallic=metallic)
    # Workbench reads diffuse_color while EEVEE reads the node tree.
    mat.diffuse_color = rgba
    MATS[name] = mat
    return mat


def register(obj, group: str | None = None):
    if group:
        GROUPS.setdefault(group, []).append(obj)
    return obj


def set_material(obj, mat_name: str):
    assign_material(obj, MATS[mat_name])
    return obj


def tube(name: str, points, radius: float, mat_name: str, group: str | None = None, parent=None):
    obj = curve_between(name, points[0], points[1], radius=radius, material=MATS[mat_name])
    spline = obj.data.splines[0]
    if len(points) > 2:
        spline.points.add(len(points) - 2)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1.0)
    if parent is not None:
        obj.parent = parent
    return register(obj, group)


def update_tube(obj, points):
    for point, co in zip(obj.data.splines[0].points, points):
        point.co = (*co, 1.0)


def text_label(name: str, body: str, location, size: float = 0.13, mat_name: str = "dark", group=None):
    data = bpy.data.curves.new(name, "FONT")
    data.body = body
    data.size = size
    data.align_x = "CENTER"
    data.align_y = "CENTER"
    data.extrude = 0.001
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    if "text_ink" not in MATS:
        ink = bpy.data.materials.new("Text ink unlit")
        ink.use_nodes = True
        nodes = ink.node_tree.nodes
        nodes.clear()
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = srgb_linear("#243247")
        output = nodes.new("ShaderNodeOutputMaterial")
        ink.node_tree.links.new(emission.outputs[0], output.inputs["Surface"])
        MATS["text_ink"] = ink
    assign_material(obj, MATS["text_ink"])
    return register(obj, group)


def visibility(group: str, visible: bool):
    for obj in GROUPS.get(group, []):
        obj.hide_render = not visible
        obj.hide_viewport = not visible


def setup_scene(profile: str = "FINAL"):
    # The shared kit owns camera/light/world construction.  The episode then
    # applies its locked bright palette and viewport delivery size.
    # Blender 5.2 builds without FFmpeg no longer expose FFMPEG as an image
    # format.  The shared bootstrap otherwise remains authoritative, so replace
    # only its video-oriented setup callback with an equivalent still setup.
    def still_render_setup(profile="FINAL", video="output.mp4", transparent=False):
        p = profile.upper()
        engine, percentage, samples, view = shared_scene_kit.PROFILES[p]
        current = bpy.context.scene
        shared_scene_kit._engine(current, engine)
        current.render.fps = shared_scene_kit.FPS
        current.render.resolution_x, current.render.resolution_y = shared_scene_kit.RES
        current.render.resolution_percentage = percentage
        try:
            current.view_settings.view_transform = view
        except (TypeError, ValueError):
            current.view_settings.view_transform = "AgX"
        current.view_settings.exposure = 0
        current.render.film_transparent = bool(transparent)
        current.render.image_settings.file_format = "PNG"
        current.render.filepath = str(shared_scene_kit.OUT / "frame.png")
        return current

    shared_scene_kit.render_setup = still_render_setup
    kit = shared_scene_kit.bootstrap(profile=profile, subject=(1.25, 0.85, 0.9), camera="wide", style="minimal", floor=True)
    scene = kit["scene"]
    camera = kit["camera"]
    target = kit["target"]
    scene.frame_start = 1
    scene.frame_end = 5351
    scene.render.fps = FPS
    scene.render.resolution_x, scene.render.resolution_y = VIEWPORT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.render.film_transparent = False
    scene.view_settings.exposure = -0.7
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except TypeError:
        pass

    for name, value in HEX.items():
        roughness = 0.34 if name in {"link1", "amber"} else 0.52
        make_material(name, value, roughness=roughness, metallic=0.03 if name in {"link1", "link2"} else 0.0)

    set_material(kit["floor"], "floor")
    world = scene.world
    world.color = srgb_linear(HEX["bg"])[:3]
    if world and world.use_nodes:
        background = world.node_tree.nodes.get("Background")
        background.inputs["Color"].default_value = srgb_linear(HEX["bg"])
        background.inputs["Strength"].default_value = 0.65

    # Stable three-quarter teaching view; all trace poses fit this shot.
    camera.location = (6.0, -7.8, 4.8)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 6.0
    target.location = (1.25, 1.0, 1.15)
    look_at(camera, target)
    camera.data.dof.use_dof = False
    return scene, camera


def make_workbench(scene):
    """Fast documented production fallback after the EEVEE benchmark."""
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except TypeError:
        pass
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.studiolight_rotate_z = 0.35
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.curvature_ridge_factor = 1.15
    shading.curvature_valley_factor = 0.75
    shading.show_specular_highlight = True
    shading.background_type = "WORLD"
    scene.world.color = srgb_linear(HEX["bg"])[:3]
    scene.display.render_aa = "16"


def build_robot(scene, camera):
    # Base frame is on the floor; shoulder/J1/J2 share the point at z=h.
    base_yaw = bpy.data.objects.new("J1_base_yaw_Rz", None)
    bpy.context.collection.objects.link(base_yaw)
    base_yaw.location = (0, 0, H)

    shoulder_pitch = bpy.data.objects.new("J2_shoulder_pitch_Ry_minus_q2", None)
    bpy.context.collection.objects.link(shoulder_pitch)
    shoulder_pitch.parent = base_yaw

    elbow_origin = bpy.data.objects.new("Frame2_elbow_origin", None)
    bpy.context.collection.objects.link(elbow_origin)
    elbow_origin.parent = shoulder_pitch
    elbow_origin.location = (L1, 0, 0)

    elbow_pitch = bpy.data.objects.new("J3_elbow_pitch_Ry_minus_q3", None)
    bpy.context.collection.objects.link(elbow_pitch)
    elbow_pitch.parent = elbow_origin

    frame3_origin = bpy.data.objects.new("Frame3_EE_origin", None)
    bpy.context.collection.objects.link(frame3_origin)
    frame3_origin.parent = elbow_pitch
    frame3_origin.location = (L2, 0, 0)

    # Pedestal and exact two-link mechanism.
    plate = set_material(add_cylinder("Base mounting plate", (0, 0, 0.055), 0.42, 0.11, 0.025), "dark")
    column = set_material(add_cylinder("Base column h=0.6m", (0, 0, 0.31), 0.24, 0.52, 0.025), "link2")
    yaw_cap = set_material(add_cylinder("J1 yaw housing", (0, 0, 0), 0.31, 0.19, 0.025), "dark")
    yaw_cap.parent = base_yaw

    shoulder_housing = set_material(add_cylinder("J2 shoulder housing", (0, 0, 0), 0.22, 0.46, 0.025), "dark")
    shoulder_housing.rotation_euler.x = math.pi / 2
    shoulder_housing.parent = base_yaw

    # add_cube() takes Blender scale (half extents), not final dimensions.
    link1 = set_material(add_cube("Link 1 L1=2.0m", (L1 / 2, 0, 0), (L1 / 2, 0.12, 0.11), 0.055), "link1")
    link1.parent = shoulder_pitch

    elbow_housing = set_material(add_cylinder("J3 elbow housing", (0, 0, 0), 0.20, 0.40, 0.025), "dark")
    elbow_housing.rotation_euler.x = math.pi / 2
    elbow_housing.parent = elbow_origin

    link2 = set_material(add_cube("Link 2 L2=1.5m", (L2 / 2, 0, 0), (L2 / 2, 0.105, 0.095), 0.05), "link2")
    link2.parent = elbow_pitch

    ee = set_material(add_point("P / Frame3 origin", (0, 0, 0), MATS["amber"], radius=0.14), "amber")
    ee.parent = frame3_origin

    # Semantic coordinate frames use the shared robotics helper.
    frame0, axes0 = add_coordinate_frame("Frame0", origin=(0, 0, 0.02), scale=0.72)
    frame1, axes1 = add_coordinate_frame("Frame1", origin=(0, 0, 0), scale=0.48)
    frame1.parent = base_yaw
    frame2, axes2 = add_coordinate_frame("Frame2", origin=(0, 0, 0), scale=0.44)
    frame2.parent = elbow_origin
    frame3, axes3 = add_coordinate_frame("Frame3", origin=(0, 0, 0), scale=0.40)
    frame3.parent = frame3_origin
    for axes in (axes0, axes1, axes2, axes3):
        for axis_name, obj in axes.items():
            set_material(obj, axis_name)
            obj.data.bevel_depth = 0.020
    for obj in [frame0, *axes0.values()]:
        register(obj, "frame0")
    for obj in [frame1, *axes1.values()]:
        register(obj, "frame1")
    for obj in [frame2, *axes2.values()]:
        register(obj, "frame2")
    for obj in [frame3, *axes3.values()]:
        register(obj, "frame3")

    # Sparse floor grid and ground radial cue keep yaw legible.
    for i in range(-3, 5):
        c = i * 0.6
        tube(f"Floor grid X {i}", [(-1.0, c, 0.012), (4.0, c, 0.012)], 0.004, "plane")
        tube(f"Floor grid Y {i}", [(c, -1.0, 0.013), (c, 4.0, 0.013)], 0.004, "plane")

    # Dynamic teaching arcs; point counts stay fixed for animation/keyframing.
    j1_arc = tube("theta1 yaw arc", [(0, 0, H + 0.20)] * 41, 0.018, "dark", "arcs")
    j2_arc = tube("theta2 shoulder arc", [(0, 0, H)] * 41, 0.018, "link1", "arcs")
    j3_arc = tube("theta3 elbow arc", [(0, 0, H)] * 41, 0.018, "inactive", "arcs")

    # Scene 4 radial vertical plane: a restrained wire grid instead of a dense overlay.
    plane_lines = []
    plane_specs = [
        [(0, 0, -H), (3.75, 0, -H), (3.75, 0, 2.55), (0, 0, 2.55), (0, 0, -H)],
        [(0, 0, 0), (3.75, 0, 0)],
        [(0, 0, 0.8), (3.75, 0, 0.8)],
        [(1.25, 0, -H), (1.25, 0, 2.55)],
        [(2.50, 0, -H), (2.50, 0, 2.55)],
    ]
    for i, points in enumerate(plane_specs):
        obj = tube(f"Radial plane guide {i}", points, 0.007 if i else 0.012, "plane", "radial_plane", base_yaw)
        plane_lines.append(obj)

    radial = tube("radial distance r", [(0, 0, H), (1, 0, H)], 0.014, "dark", "projections")
    vertical = tube("vertical projection z-h", [(1, 0, H), (1, 0, 1)], 0.014, "z", "projections")
    h_line = tube("shoulder height h", [(-0.28, 0, 0), (-0.28, 0, H)], 0.012, "inactive", "projections")
    projection_point = set_material(add_point("P floor projection", (1, 0, H), MATS["dark"], radius=0.055), "dark")
    register(projection_point, "projections")

    # Reference wires clarify which downstream links each pitch joint moves.
    ghost1 = tube("Shoulder reference link1", [(0, 0, H), (1, 0, H)], 0.032, "ghost", "ghost")
    ghost2 = tube("Shoulder reference link2", [(1, 0, H), (2, 0, H)], 0.028, "ghost", "ghost")
    ghost_joints = [
        register(set_material(add_point(f"Reference joint {i}", (0, 0, H), MATS["ghost"], radius=0.075), "ghost"), "ghost")
        for i in range(3)
    ]

    # Compact object labels only; equations/captions remain the Manim layer.
    labels = {
        "J1": text_label("J1 label", "J1", (-0.42, -0.16, H + 0.06), 0.15),
        "J2": text_label("J2 label", "J2", (0.25, -0.18, H + 0.22), 0.15),
        "J3": text_label("J3 label", "J3", (L1, 0, H), 0.15),
        "P": text_label("P label", "P = O{3}", (L1 + L2, 0, H), 0.16, "amber"),
        "F0": text_label("Frame0 label", "{0}", (-0.18, -0.22, 0.22), 0.12, group="frame_labels"),
        "F1": text_label("Frame1 label", "{1}", (0, 0, H), 0.12, group="frame_labels"),
        "F2": text_label("Frame2 label", "{2}", (L1, 0, H), 0.12, group="frame_labels"),
        "F3": text_label("Frame3 label", "", (L1 + L2, 0, H), 0.12, group="frame_labels"),
        "r": text_label("Radial label", "r", (1, 0, H), 0.12, group="projection_labels"),
        "zh": text_label("Height label", "z-h", (1, 0, 1), 0.11, "z", group="projection_labels"),
        "h": text_label("Base height label", "h", (-0.28, 0, H / 2), 0.11, "inactive", group="projection_labels"),
        "X": text_label("X axis label", "X", (0.82, 0, 0.02), 0.105, "x", group="axis_labels"),
        "Y": text_label("Y axis label", "Y", (0, 0.82, 0.02), 0.105, "y", group="axis_labels"),
        "Z": text_label("Z axis label", "Z", (0, 0, 0.82), 0.105, "z", group="axis_labels"),
    }
    for obj in labels.values():
        obj.rotation_euler = camera.rotation_euler

    return locals()


def joint_positions(q):
    q1, q2, q3 = q
    c, s = math.cos(q1), math.sin(q1)
    p0 = Vector((0, 0, H))
    p1 = Vector((L1 * math.cos(q2) * c, L1 * math.cos(q2) * s, H + L1 * math.sin(q2)))
    reach = L1 * math.cos(q2) + L2 * math.cos(q2 + q3)
    p2 = Vector((reach * c, reach * s, H + L1 * math.sin(q2) + L2 * math.sin(q2 + q3)))
    return p0, p1, p2


def arc_points(record):
    q1, q2, q3 = record["q_rad"]
    p0, p1, _ = [Vector(v) for v in record["joints"]]
    yaw = [Vector((0.47 * math.cos(q1 * i / 40), 0.47 * math.sin(q1 * i / 40), H + 0.20)) for i in range(41)]
    shoulder = [
        p0 + Vector((0.43 * math.cos(q2 * i / 40) * math.cos(q1), 0.43 * math.cos(q2 * i / 40) * math.sin(q1), 0.43 * math.sin(q2 * i / 40)))
        for i in range(41)
    ]
    elbow = []
    for i in range(41):
        elevation = q2 + q3 * i / 40
        elbow.append(p1 + Vector((0.38 * math.cos(elevation) * math.cos(q1), 0.38 * math.cos(elevation) * math.sin(q1), 0.38 * math.sin(elevation))))
    return yaw, shoulder, elbow


def apply_record(record, objects):
    q1, q2, q3 = record["q_rad"]
    scene_no, beat, u = record["scene"], record["beat"], record["u"]
    objects["base_yaw"].rotation_euler.z = q1
    objects["shoulder_pitch"].rotation_euler.y = -q2
    objects["elbow_pitch"].rotation_euler.y = -q3
    bpy.context.view_layer.update()

    p0, p1, p2 = [Vector(v) for v in record["joints"]]
    yaw, shoulder, elbow = arc_points(record)
    update_tube(objects["j1_arc"], yaw)
    update_tube(objects["j2_arc"], shoulder)
    update_tube(objects["j3_arc"], elbow)

    # Scene-specific hierarchy: S1 introduces joints, S4 adds radial plane and frames.
    visibility("radial_plane", scene_no == 4)
    visibility("projections", scene_no == 4)
    visibility("projection_labels", scene_no == 4)
    visibility("frame_labels", scene_no == 4)
    visibility("frame0", scene_no == 4)
    visibility("frame1", scene_no == 4)
    visibility("frame2", scene_no == 4 and beat == "B08")
    visibility("frame3", scene_no == 4 and beat == "B08")

    if scene_no == 1:
        objects["j1_arc"].hide_render = objects["j1_arc"].hide_viewport = beat == "B01" and u < 0.18
        objects["j2_arc"].hide_render = objects["j2_arc"].hide_viewport = beat == "B01" or (beat == "B02" and u < 0.10)
        objects["j3_arc"].hide_render = objects["j3_arc"].hide_viewport = beat == "B01" or (beat == "B02" and u < 0.48)
    else:
        objects["j1_arc"].hide_render = objects["j1_arc"].hide_viewport = False
        objects["j2_arc"].hide_render = objects["j2_arc"].hide_viewport = beat != "B08"
        objects["j3_arc"].hide_render = objects["j3_arc"].hide_viewport = beat != "B08" or u < 0.44

    # Trace-derived radial projection and height markers.
    radial_end = Vector((p2.x, p2.y, H))
    update_tube(objects["radial"], [p0, radial_end])
    update_tube(objects["vertical"], [radial_end, p2])
    update_tube(objects["h_line"], [(-0.28, 0, 0), (-0.28, 0, H)])
    objects["projection_point"].location = radial_end

    labels = objects["labels"]
    labels["J1"].location = (-0.40, -0.22, H - 0.05)
    labels["J2"].location = p0 + Vector((0.26, -0.10, 0.32))
    labels["J3"].location = p1 + Vector((0.2, -0.45, 0.35))
    labels["P"].location = p2 + Vector((0.12, -0.06, 0.24))
    labels["F1"].location = p0 + Vector((-0.18, 0.12, 0.38))
    labels["F2"].location = p1 + Vector((-0.16, 0.10, 0.34))
    labels["F3"].location = p2 + Vector((-0.16, 0.10, 0.36))
    labels["r"].location = (p0 + radial_end) / 2 + Vector((0, 0, -0.13))
    labels["zh"].location = (radial_end + p2) / 2 + Vector((0.12, 0.04, 0))
    labels["h"].location = Vector((-0.40, 0, H / 2))
    for label in labels.values():
        label.rotation_euler = objects["camera"].rotation_euler

    # Shoulder reference shows both downstream links; elbow reference shows only link 2.
    ghost_visible = scene_no == 4 and beat == "B08" and 0.12 <= u < 0.78
    visibility("ghost", ghost_visible)
    if ghost_visible:
        reference_q = (math.radians(65), math.radians(25), math.radians(-40)) if u < 0.44 else (math.radians(65), math.radians(50), math.radians(-40))
        g0, g1, g2 = joint_positions(reference_q)
        update_tube(objects["ghost1"], [g0, g1])
        update_tube(objects["ghost2"], [g1, g2])
        for obj, position in zip(objects["ghost_joints"], (g0, g1, g2)):
            obj.location = position
        objects["ghost1"].hide_render = objects["ghost1"].hide_viewport = u >= 0.44

    # Base XYZ letters are only needed when the coordinate chain is introduced.
    visibility("axis_labels", scene_no == 4)
    bpy.context.view_layer.update()


def stage_signature(record):
    scene_no, beat, u = record["scene"], record["beat"], record["u"]
    if scene_no == 1:
        stage = (beat, u >= 0.18, u >= 0.10 if beat == "B02" else False, u >= 0.48 if beat == "B02" else False)
    else:
        stage = (beat, u >= 0.12, u >= 0.44, u >= 0.78)
    return (scene_no, tuple(round(v, 7) for v in record["q_rad"]), stage)


def keyframe_record(objects, frame):
    for obj in (objects["base_yaw"], objects["shoulder_pitch"], objects["elbow_pitch"]):
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    for obj in objects["labels"].values():
        obj.keyframe_insert(data_path="location", frame=frame)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    objects["projection_point"].keyframe_insert(data_path="location", frame=frame)
    for obj in (objects["j1_arc"], objects["j2_arc"], objects["j3_arc"], objects["radial"], objects["vertical"], objects["h_line"], objects["ghost1"], objects["ghost2"]):
        for point in obj.data.splines[0].points:
            point.keyframe_insert(data_path="co", frame=frame)
    for obj in objects["ghost_joints"]:
        obj.keyframe_insert(data_path="location", frame=frame)
    for group in GROUPS.values():
        for obj in group:
            obj.keyframe_insert(data_path="hide_render", frame=frame)
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)
    for obj in (objects["j1_arc"], objects["j2_arc"], objects["j3_arc"]):
        obj.keyframe_insert(data_path="hide_render", frame=frame)
        obj.keyframe_insert(data_path="hide_viewport", frame=frame)


def add_markers(scene, timeline):
    for beat in timeline["beats"]:
        scene.timeline_markers.new(beat["id"], frame=beat["start_frame"] + 1)


def save_blend(scene):
    scene.render.filepath = "//frames/"
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.shading.color_type = "MATERIAL"
                area.spaces.active.overlay.show_overlays = False
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))


def validate_geometry(record, objects):
    actual_ee = objects["frame3_origin"].matrix_world.translation
    expected = Vector(record["ee"])
    ee_error = (actual_ee - expected).length
    actual_elbow = objects["elbow_origin"].matrix_world.translation
    elbow_error = (actual_elbow - Vector(record["joints"][1])).length
    return ee_error, elbow_error


def render_previews(scene, objects, records):
    previews = [
        (0, "preview_s1_yaw_start.png"),
        (602, "preview_s1_shoulder_peak.png"),
        (3009, "preview_s4_radial_plane.png"),
        (3745, "preview_s4_frame3_endpoint.png"),
    ]
    timings = []
    for frame_index, filename in previews:
        record = records[frame_index]
        scene.frame_set(frame_index + 1)
        apply_record(record, objects)
        scene.render.filepath = str(OUT / filename)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        elapsed = time.perf_counter() - started
        timings.append(elapsed)
        print(f"PREVIEW {filename}: {elapsed:.3f}s", flush=True)
    report = {
        "engine": scene.render.engine,
        "resolution": list(VIEWPORT),
        "frames": [f for f, _ in previews],
        "seconds": timings,
        "mean_seconds": sum(timings) / len(timings),
    }
    (OUT / "preview_benchmark.json").write_text(json.dumps(report, indent=2))
    return report


def render_sequence(scene, objects, records, do_render: bool):
    mapping: list[int | None] = []
    cache = {}
    max_ee_error = 0.0
    max_elbow_error = 0.0
    started = time.perf_counter()
    previous_signature = None

    for frame_index, record in enumerate(records):
        if record["scene"] not in BLENDER_SCENES or record["tool"] != "B":
            mapping.append(None)
            continue

        signature = stage_signature(record)
        next_signature = None
        if frame_index + 1 < len(records):
            nxt = records[frame_index + 1]
            if nxt["scene"] in BLENDER_SCENES and nxt["tool"] == "B":
                next_signature = stage_signature(nxt)

        scene.frame_set(frame_index + 1)
        apply_record(record, objects)
        ee_error, elbow_error = validate_geometry(record, objects)
        max_ee_error = max(max_ee_error, ee_error)
        max_elbow_error = max(max_elbow_error, elbow_error)
        if ee_error > 2e-6 or elbow_error > 2e-6:
            raise AssertionError(f"FK mismatch at trace frame {frame_index}: ee={ee_error}, elbow={elbow_error}")

        if signature != previous_signature or signature != next_signature:
            keyframe_record(objects, frame_index + 1)
        previous_signature = signature

        if signature not in cache:
            index = len(cache)
            cache[signature] = index
            if do_render:
                scene.render.filepath = str(FRAMES / f"{index:05d}.png")
                bpy.ops.render.render(write_still=True)
            if index % 100 == 0:
                print(f"PROGRESS trace={frame_index}/{len(records) - 1} unique={index} elapsed={time.perf_counter() - started:.1f}s", flush=True)
        mapping.append(cache[signature])

    if len(mapping) != 5351:
        raise AssertionError(f"Expected 5351 frame-map entries, got {len(mapping)}")

    # Exact trace samples should not be eased a second time by Blender.
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = "CONSTANT"

    elapsed = time.perf_counter() - started
    (OUT / "frame_map.json").write_text(json.dumps(mapping, separators=(",", ":")))
    validation = {
        "evidence": "computed ideal kinematics / trace playback; no dynamics or hardware measurement",
        "trace_frames": len(records),
        "mapped_blender_frames": sum(value is not None for value in mapping),
        "null_non_blender_frames": sum(value is None for value in mapping),
        "unique_rendered_frames": len(cache),
        "max_end_effector_error_m": max_ee_error,
        "max_elbow_error_m": max_elbow_error,
        "link_lengths_m": [L1, L2],
        "shoulder_height_m": H,
        "resolution": list(VIEWPORT),
        "fps": FPS,
        "render_engine": scene.render.engine,
        "render_seconds": elapsed,
        "blender": bpy.app.version_string,
    }
    (OUT / "geometry_validation.json").write_text(json.dumps(validation, indent=2))
    return mapping, validation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="render four EEVEE review frames")
    parser.add_argument("--render", action="store_true", help="render the deduplicated production sequence")
    parser.add_argument("--workbench", action="store_true", help="use Workbench for the production sequence")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])

    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    trace = json.loads(TRACE_PATH.read_text())
    timeline = json.loads(TIMELINE_PATH.read_text())
    records = trace["frames"]
    if len(records) != timeline["frames"] or timeline["frames"] != 5351 or timeline["fps"] != FPS:
        raise AssertionError("Locked timeline/trace contract changed")
    if (trace["L1"], trace["L2"], trace["h"]) != (L1, L2, H):
        raise AssertionError("Locked robot dimensions changed")

    scene, camera = setup_scene("FINAL")
    objects = build_robot(scene, camera)
    add_markers(scene, timeline)

    if args.preview:
        report = render_previews(scene, objects, records)
        print("PREVIEW_COMPLETE", json.dumps(report), flush=True)
        return

    if args.workbench:
        make_workbench(scene)
    mapping, validation = render_sequence(scene, objects, records, args.render)
    first = next(i for i, value in enumerate(mapping) if value is not None)
    scene.frame_set(first + 1)
    apply_record(records[first], objects)
    save_blend(scene)
    print("COMPLETE", json.dumps(validation), flush=True)


if __name__ == "__main__":
    main()
