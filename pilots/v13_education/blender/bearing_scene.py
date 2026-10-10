"""Procedural deep-groove ball bearing concept scene for the V13 lesson pilot."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import bpy
from mathutils import Vector

BLENDER_KIT = REPO_ROOT / "core/blender-robotics-simulation-skill/templates"
if str(BLENDER_KIT) not in sys.path:
    sys.path.insert(0, str(BLENDER_KIT))
from studio_utils import set_interpolation


def args_after_separator():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--timeline", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--still-frame", type=int, default=0,
                        help="render one review still instead of the full animation")
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(values)


def material(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def text_overlay(camera, body, name, location, mat, size=.17):
    bpy.ops.object.text_add()
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.size = size
    obj.data.extrude = .001
    obj.data.materials.append(mat)
    obj.parent = camera
    obj.location = location
    obj.rotation_euler = (0, 0, 0)
    return obj


def overlay_panel(camera, mat):
    bpy.ops.mesh.primitive_plane_add(size=2)
    panel = bpy.context.object
    panel.name = "part_label_panel"
    panel.parent = camera
    panel.location = (2.95, 1.40, -2.05)
    panel.scale = (.85, .94, 1)
    panel.data.materials.append(mat)
    return panel


def camera_rotation_indicator(camera, accent, white, phase, frame_end):
    """Camera-space counter-clockwise cue for the positive local-Z shaft rotation."""
    cx, cy, radius, z = -3.05, 1.34, .31, -2.15
    curve_data = bpy.data.curves.new("inner_race_rotation_arc", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.bevel_depth = .022
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new("POLY")
    points = 36
    spline.points.add(points - 1)
    start, stop = math.radians(-135), math.radians(105)
    for i, point in enumerate(spline.points):
        angle = start + (stop - start) * i / (points - 1)
        point.co = (cx + radius * math.cos(angle), cy + radius * math.sin(angle), z, 1)
    arc = bpy.data.objects.new("inner_race_rotation_direction_ccw", curve_data)
    bpy.context.scene.collection.objects.link(arc)
    arc.parent = camera
    arc.data.materials.append(accent)

    angle = stop
    tip = Vector((cx + radius * math.cos(angle), cy + radius * math.sin(angle), z))
    tangent = Vector((-math.sin(angle), math.cos(angle), 0)).normalized()
    normal = Vector((-tangent.y, tangent.x, 0))
    vertices = [tip, tip - tangent * .19 + normal * .11, tip - tangent * .19 - normal * .11]
    mesh = bpy.data.meshes.new("rotation_arrowhead_mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2)])
    head = bpy.data.objects.new("rotation_arrowhead_ccw", mesh)
    bpy.context.scene.collection.objects.link(head)
    head.parent = camera
    head.data.materials.append(accent)

    label = text_overlay(camera, "내륜 회전 방향", "inner_race_rotation_label",
                         (-2.62, 1.27, z), white, .13)
    for obj in (arc, head, label):
        for frame, hidden in ((1, True), (max(1, phase["presentation_start_frame"] - 1), True),
                              (phase["presentation_start_frame"], False),
                              (phase["presentation_end_frame"] - 1, False),
                              (min(frame_end, phase["presentation_end_frame"]), True),
                              (frame_end, True)):
            obj.hide_render = hidden
            obj.keyframe_insert(data_path="hide_render", frame=frame)
        set_interpolation(obj, "CONSTANT", paths=["hide_render"])


def key_visibility(obj, frames, visible):
    obj.hide_render = not visible
    obj.keyframe_insert(data_path="hide_render", frame=frames[0])
    obj.hide_render = not visible
    obj.keyframe_insert(data_path="hide_render", frame=frames[1])


def make_scene(manifest, timeline, output, width, height, fps, samples=16, still_frame=0):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = samples
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.frame_start = 1
    scene.frame_end = timeline["total_frames"]
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.filepath = str(output)
    scene.render.film_transparent = False
    scene.world.color = (.018, .026, .043)
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.color_mode = "RGB"

    steel = material("Satin chromium steel", (.33, .49, .66), .82, .24)
    blue_steel = material("Inner race blue steel", (.08, .37, .68), .78, .22)
    ceramic = material("Rolling elements", (.77, .84, .9), .55, .16)
    cage_mat = material("Cage polymer brass", (.91, .43, .12), .55, .28)
    ground_mat = material("Stage", (.025, .04, .065), .16, .55)
    accent = material("Load path highlight", (1.0, .22, .12), .25, .33)
    white = material("Labels", (.83, .91, 1), .1, .5)
    panel_mat = material("Label panel", (.014, .025, .045), .05, .8)

    from core.visual_primitives.blender.exploded_assembly import create_ring, create_roller_set

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -1.15))
    bpy.context.object.name = "ground"
    bpy.context.object.data.materials.append(ground_mat)
    outer = create_ring(bpy, "outer_race_fixed", 1.66, .20, steel)
    inner = create_ring(bpy, "inner_race_rotating", .82, .17, blue_steel)
    cage = create_ring(bpy, "separator_cage", 1.22, .055, cage_mat, segments=64, ring_segments=12)
    rollers = create_roller_set(bpy, ceramic, count=8, pitch_radius=1.22, roller_radius=.19, segments=24, rings=12)
    orbit = bpy.data.objects.new("idealized_ball_orbit", None)
    scene.collection.objects.link(orbit)
    for ball in rollers:
        world = ball.matrix_world.copy()
        ball.parent = orbit
        ball.matrix_parent_inverse = orbit.matrix_world.inverted()
        ball.matrix_world = world
        ball.rotation_mode = "XYZ"

    spin_ball = rollers[0]
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8,
                                    major_radius=.145, minor_radius=.024, location=(0,0,0))
    spin_marker = bpy.context.object
    spin_marker.name = "rolling_element_spin_marker"
    spin_marker.parent = spin_ball
    # A small high-contrast surface dot makes ball rotation observable.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=.045,
                                         location=(0,0,0))
    spin_marker = bpy.context.object
    spin_marker.name = "rolling_element_spin_marker"
    spin_marker.parent = spin_ball
    spin_marker.location = (0, -.17, .07)
    spin_marker.data.materials.append(accent)

    # The shaft and housing are cutaway visual references, not CAD geometry.
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.60, depth=2.0, location=(0, 0, 0))
    shaft = bpy.context.object
    shaft.name = "shaft_reference"
    shaft.data.materials.append(blue_steel)
    for poly in shaft.data.polygons:
        poly.use_smooth = True
    # A camera-facing shaft-end pointer is a teaching cue for shaft rotation.
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=.12, radius2=0, depth=.26,
                                    location=(0,0,0))
    shaft_pointer = bpy.context.object
    shaft_pointer.name = "shaft_rotation_pointer"
    shaft_pointer.parent = shaft
    shaft_pointer.location = (0, -.66, 0)
    shaft_pointer.rotation_euler[0] = math.pi/2
    shaft_pointer.data.materials.append(accent)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=.105,
                                         location=(0, 0, 0))
    shaft_face_marker = bpy.context.object
    shaft_face_marker.name = "rotating_shaft_face_marker"
    shaft_face_marker.parent = shaft
    shaft_face_marker.location = (.38, 0, 1.035)
    shaft_face_marker.data.materials.append(accent)
    bpy.ops.mesh.primitive_torus_add(major_segments=96, minor_segments=16, major_radius=2.08,
                                    minor_radius=.12, location=(0, 0, 0))
    housing = bpy.context.object
    housing.name = "housing_reference"
    housing.data.materials.append(steel)
    for poly in housing.data.polygons:
        poly.use_smooth = True

    # Rotate the inner race and the cage. Balls circulate as an idealized motion cue;
    # no solver contact forces or friction values are computed in this scene.
    beat_phases = {beat["phase_id"]: next(phase for phase in timeline["phases"]
                      if phase["phase_id"] == beat["phase_id"]) for beat in manifest["beats"]}
    load_phase = beat_phases.get("load_path")
    hold_start = load_phase["presentation_start_frame"] if load_phase else scene.frame_end + 1
    hold_end = load_phase["presentation_end_frame"]-1 if load_phase else scene.frame_end
    hold_frames = max(0, hold_end-hold_start)

    def rotation_with_explanatory_hold(obj, turns, axis=2):
        moving_frames = max(1, scene.frame_end-1-hold_frames)
        held_angle = math.tau*turns*(hold_start-1)/moving_frames
        for frame, angle in ((1, 0), (hold_start, held_angle),
                             (hold_end, held_angle), (scene.frame_end, math.tau*turns)):
            obj.rotation_euler[axis] = angle
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    rotation_with_explanatory_hold(inner, 2.4)
    rotation_with_explanatory_hold(shaft, 2.4)
    rotation_with_explanatory_hold(cage, 1.51)
    rotation_with_explanatory_hold(orbit, 1.51)
    for ball in rollers:
        rotation_with_explanatory_hold(ball, 1.2, axis=1)

    camera_data = bpy.data.cameras.new("lesson_camera")
    camera = bpy.data.objects.new("lesson_camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (4.1, -5.6, 4.4)
    direction = Vector((.5, 0, 0)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 7.7
    scene.camera = camera

    for loc, energy, size in [((2,-4,6), 1200, 5), ((-4,-1,2), 750, 4), ((1,4,4), 1300, 3)]:
        light_data = bpy.data.lights.new("studio_softbox", "AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new("studio_softbox", light_data)
        scene.collection.objects.link(light)
        light.location = loc
        light.rotation_euler = (Vector((0,0,0))-light.location).to_track_quat("-Z", "Y").to_euler()

    # The exploded assembly state is controlled by the same manifest phase intervals.
    phases = {phase["phase_id"]: phase for phase in timeline["phases"]}
    beats = {beat["phase_id"]: beat for beat in manifest["beats"]}
    rotation_phase = phases.get("rotation")
    if rotation_phase:
        camera_rotation_indicator(camera, accent, white, rotation_phase, scene.frame_end)
    exploded_phase = phases.get("exploded")
    reassemble_phase = phases.get("parts_reassemble")
    if exploded_phase and reassemble_phase:
        explode_at = exploded_phase["presentation_start_frame"] + 12
        reassembly_start = reassemble_phase["presentation_start_frame"]
        reassembly_end = reassemble_phase["presentation_end_frame"] - 1
        assembly_frames = reassembly_end - reassembly_start
        def staged_reassembly(obj, offset, landing_frame):
            base = obj.location.copy()
            return_frame = min(reassembly_end, max(reassembly_start + 1, landing_frame))
            for frame, location in ((1, base), (explode_at, base + Vector((0,0,offset))),
                                    (reassembly_start, base + Vector((0,0,offset))),
                                    (return_frame, base), (reassembly_end, base)):
                obj.location = location
                obj.keyframe_insert(data_path="location", frame=frame)

        moving_parts = [(outer, .24, .34), (inner, -.34, .18), (cage, .43, .78)]
        for index, (obj, offset, return_fraction) in enumerate(moving_parts):
            staged_reassembly(obj, offset,
                              reassembly_start + round(assembly_frames*(.18 + index*.24)))
        for index, ball in enumerate(rollers):
            offset = .22 if index % 2 else -.22
            staged_reassembly(ball, offset,
                              reassembly_start + round(assembly_frames*(.18 + (index%4)*.13)))

    # A fixed, clearly directed radial load arrow appears only in the load-path beat.
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=.10, radius2=0, depth=.34,
                                    location=(-1.80, 0, .38))
    arrow_tip = bpy.context.object
    arrow_tip.name = "radial_load_arrow_tip"
    arrow_tip.rotation_euler[1] = math.pi/2
    arrow_tip.data.materials.append(accent)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=.045, depth=.48,
                                        location=(-2.22, 0, .38))
    arrow_shaft = bpy.context.object
    arrow_shaft.name = "radial_load_arrow_shaft"
    arrow_shaft.rotation_euler[1] = math.pi/2
    arrow_shaft.data.materials.append(accent)
    loaded_ball = rollers[4]
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8, major_radius=.235,
                                    minor_radius=.035, location=loaded_ball.location)
    contact_highlight = bpy.context.object
    contact_highlight.name = "load_contact_highlight"
    contact_highlight.data.materials.append(accent)
    contact_highlight.parent = orbit
    contact_highlight.location = loaded_ball.location.copy()
    load_phase = phases.get("load_path")
    load_range = (load_phase["presentation_start_frame"], load_phase["presentation_end_frame"]-1) if load_phase else (1,0)
    for obj in (arrow_tip, arrow_shaft, contact_highlight):
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=1)
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_render", frame=load_range[0])
        obj.keyframe_insert(data_path="hide_render", frame=load_range[1])
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=min(scene.frame_end, load_range[1]+1))

    # Labels and evidence boundary are camera-attached and keyed to the relevant beats.
    overlay_panel(camera, panel_mat)
    font = None
    korean_font = Path("C:/Windows/Fonts/malgun.ttf")
    if korean_font.is_file():
        font = bpy.data.fonts.load(str(korean_font))
    labels = [
        ("단열 깊은 홈 볼 베어링", (2.20, 1.86, -1.95)),
        ("내륜 / 축과 함께 회전", (2.20, 1.53, -1.95)),
        ("볼 / 궤도 사이에서 구름", (2.20, 1.20, -1.95)),
        ("케이지 / 볼 간격 유지", (2.20, .87, -1.95)),
        ("개념 동작 - 접촉 해석 아님", (2.20, .54, -1.95)),
    ]
    for body, location in labels:
        label = text_overlay(camera, body, "label_"+body[:8].replace(" ", "_"), location, white, .16)
        if font is not None:
            label.data.font = font

    scene.render.filepath = str(output)
    scene.frame_set(max(1, min(scene.frame_end, still_frame or 1)))
    bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix(".blend")))
    if still_frame:
        scene.render.image_settings.media_type = "IMAGE"
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(output.with_name(f"{output.stem}_frame_{still_frame:04d}.png"))
        bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)


def main():
    args = args_after_separator()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    timeline = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    make_scene(manifest, timeline, Path(args.output), args.width, args.height, args.fps,
               args.samples, args.still_frame)


if __name__ == "__main__":
    main()
