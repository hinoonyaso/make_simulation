"""Bright studio-floor production kit (validated in pilots/01_teb_reference).

Look: light concrete tiles, soft area lights, AgX Punchy, EEVEE, native 30 fps, full frame.
Lessons encoded here:
- Strong emission desaturates under AgX: keep emission strength ~1-2 and saturate the colour instead.
- World tone ~ far-floor tone so the horizon dissolves instead of showing a seam.
- Exact top view: Track-To degenerates when looking straight down; look() blends up Z->Y.
- Crane: pull distance back early, rotate later, so the lens never passes close over props.
- Curve reveal: bevel_factor mapping SEGMENTS is not proportional to point index; key length fractions.
"""
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

from animation_utils import set_interpolation
from geometry_utils import add_cube, add_cylinder, add_sphere, apply_bevel
from material_utils import assign_material, principled_material
from robotics_visual_utils import add_trajectory, create_emission_material

FPS = 30
PROFILES = {"PREVIEW": ((960, 540), 16, False), "FINAL": ((1920, 1080), 64, True),
            "DELIVERY": ((2560, 1440), 96, True)}
SENSOR = 36.0
STUDIO = {"band": (0.42, 0.12, 0.95, 1), "trail": (0.04, 0.45, 0.85, 1), "goal": (0.05, 0.63, 0.30, 1),
          "drum": (0.62, 0.09, 0.025, 1), "drum_lid": (0.48, 0.07, 0.02, 1)}
BUNDLE = Path(__file__).resolve().parents[3]


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------- scene ----------
def setup_studio(profile="PREVIEW", frames=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    (w, h), samples, final = PROFILES[profile]
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = w, h, 100
    s.render.fps = FPS
    s.frame_start, s.frame_end = 1, frames
    s.eevee.taa_render_samples = samples
    for attr, value in (("use_raytracing", True), ("use_shadows", True), ("use_gtao", True)):
        if hasattr(s.eevee, attr):
            setattr(s.eevee, attr, value)
    s.render.use_motion_blur = final
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    world = bpy.data.worlds.new("Studio")
    s.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.66, 0.67, 0.69, 1)
    bg.inputs["Strength"].default_value = 0.42
    return s


def add_area_light(name, location, energy, size, target=(0, 0, 0)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size, data.shape = energy, size, "DISK"
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    return obj


def studio_lights():
    return [add_area_light("Key", (-1.5, 2.5, 5.5), 1600, 3.5),
            add_area_light("Fill", (3.0, -3.5, 4.0), 350, 6.0),
            add_area_light("Rim", (4.0, 3.0, 2.0), 400, 2.5, target=(0, 0, 0.2))]


def concrete_material(tile=0.6):
    mat = bpy.data.materials.new("StudioConcrete")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.0
    brick.inputs["Scale"].default_value = 1 / tile
    brick.inputs["Brick Width"].default_value = 1.0
    brick.inputs["Row Height"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.004
    brick.inputs["Color1"].default_value = (0.30, 0.31, 0.32, 1)
    brick.inputs["Color2"].default_value = (0.36, 0.365, 0.37, 1)
    brick.inputs["Mortar"].default_value = (0.17, 0.175, 0.18, 1)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 8.0
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.42
    rough.inputs["To Max"].default_value = 0.78
    bump_tile = nt.nodes.new("ShaderNodeBump")
    bump_tile.inputs["Strength"].default_value = 0.25
    bump_grain = nt.nodes.new("ShaderNodeBump")
    bump_grain.inputs["Strength"].default_value = 0.06
    link = nt.links.new
    link(coord.outputs["Object"], brick.inputs["Vector"])
    link(coord.outputs["Object"], noise.inputs["Vector"])
    link(brick.outputs["Color"], bsdf.inputs["Base Color"])
    link(noise.outputs["Fac"], rough.inputs["Value"])
    link(rough.outputs["Result"], bsdf.inputs["Roughness"])
    link(brick.outputs["Fac"], bump_tile.inputs["Height"])
    link(noise.outputs["Fac"], bump_grain.inputs["Height"])
    link(bump_tile.outputs["Normal"], bump_grain.inputs["Normal"])
    link(bump_grain.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def add_studio_floor(size=160):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Floor"
    assign_material(floor, concrete_material())
    return floor


# ---------- props ----------
def add_corridor(half_width, half_length=3.9, height=0.32):
    wall = principled_material("WallPanel", (0.86, 0.87, 0.88, 1), roughness=0.35)
    trim = principled_material("WallTrim", (0.10, 0.11, 0.13, 1), roughness=0.5)
    for side in (-1, 1):
        y = side * (half_width + 0.03)
        assign_material(add_cube(f"Wall{side}", (0, y, height / 2), (half_length, 0.03, height / 2), bevel=0.012), wall)
        assign_material(add_cube(f"WallTrim{side}", (0, y, 0.015), (half_length, 0.034, 0.015), bevel=0.004), trim)


def add_drum(center, radius, height=0.58):
    mat = principled_material("Drum", STUDIO["drum"], roughness=0.38)
    drum = add_cylinder("Drum", (center[0], center[1], height / 2), radius=radius, depth=height, bevel=0.02)
    assign_material(drum, mat)
    for z in (0.31 * height, 0.69 * height):
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.012, location=(center[0], center[1], z))
        assign_material(bpy.context.object, mat)
    lid = add_cylinder("DrumLid", (center[0], center[1], height + 0.005), radius=radius * 0.82, depth=0.012, bevel=0.004)
    assign_material(lid, principled_material("DrumLid", STUDIO["drum_lid"], roughness=0.45))
    return drum


def add_floor_dashes(x0, x1, y=0.0, dash=0.1, gap=0.1):
    mat = principled_material("PathDash", (0.25, 0.27, 0.30, 1), roughness=0.6)
    x, i = x0, 0
    while x + dash <= x1 + 1e-9:
        assign_material(add_cube(f"Dash{i}", (x + dash / 2, y, 0.0015), (dash / 2, 0.008, 0.0015), bevel=0), mat)
        x += dash + gap; i += 1


def add_goal_ring(xy, radius=0.16):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.012, location=(xy[0], xy[1], 0.004))
    ring = bpy.context.object
    ring.scale.z = 0.25
    assign_material(ring, create_emission_material("Goal", STUDIO["goal"], 1.2))
    return ring


# ---------- robots ----------
def _import_stl(path, name, mat, parent, location=(0, 0, 0), rotation=(0, 0, 0)):
    bpy.ops.wm.stl_import(filepath=str(path), global_scale=0.001)
    obj = bpy.context.selected_objects[0]
    obj.name = name
    obj.location, obj.rotation_euler = location, rotation
    obj.parent = parent
    assign_material(obj, mat)
    bpy.ops.object.shade_smooth_by_angle()
    return obj


def load_turtlebot3(variant="waffle_pi"):
    """TurtleBot3 from assets/turtlebot3 (Apache-2.0), placed per turtlebot3_<variant>.urdf.

    Returns (root, wheel_pivots, geometry). Root origin = base_footprint; +x forward.
    Wheel pivots spin about +y; positive angle rolls the robot forward.
    """
    assert variant in ("waffle", "waffle_pi"), "only waffle variants are wired here"
    meshes = BUNDLE / "assets/turtlebot3/meshes"
    root = bpy.data.objects.new("TurtleBot3", None)
    bpy.context.collection.objects.link(root)
    chassis = principled_material("TB3Chassis", (0.075, 0.078, 0.085, 1), metallic=0.2, roughness=0.38)
    rubber = principled_material("TB3Tyre", (0.02, 0.02, 0.022, 1), roughness=0.82)
    sensor = principled_material("TB3Sensor", (0.06, 0.065, 0.07, 1), metallic=0.3, roughness=0.3)
    z0 = 0.010  # base_joint: base_link is 10 mm above base_footprint
    _import_stl(meshes / f"bases/{variant}_base.stl", "TB3Base", chassis, root, (-0.064, 0, z0))
    _import_stl(meshes / "sensors/lds.stl", "TB3Lidar", sensor, root, (-0.064, 0, z0 + 0.122))
    wheels = []
    for side, name in ((1, "left"), (-1, "right")):
        pivot = bpy.data.objects.new(f"TB3Wheel_{name}", None)
        bpy.context.collection.objects.link(pivot)
        pivot.parent = root
        pivot.location = (0.0, side * 0.144, z0 + 0.023)
        _import_stl(meshes / f"wheels/{name}_tire.stl", f"TB3Tyre_{name}", rubber, pivot, rotation=(0, 0, 0))
        wheels.append(pivot)
    alu = principled_material("TB3Caster", (0.7, 0.72, 0.75, 1), metallic=1.0, roughness=0.25)
    for side in (1, -1):
        c = add_sphere(f"TB3Caster{side}", (-0.177, side * 0.064, 0.006), 0.006)
        assign_material(c, alu)
        c.parent = root
    return root, wheels, {"wheel_radius": 0.033, "wheel_separation": 0.288, "variant": variant}


def build_procedural_amr():
    """Stylised AMR fallback (0.38 x 0.31 m body, wheel radius 0.10 m, separation 0.42 m)."""
    root = bpy.data.objects.new("AMR", None)
    bpy.context.collection.objects.link(root)
    white = principled_material("AMRShell", (0.88, 0.89, 0.90, 1), roughness=0.28)
    dark = principled_material("AMRDark", (0.06, 0.065, 0.075, 1), roughness=0.55)
    rubber = principled_material("Tyre", (0.025, 0.025, 0.028, 1), roughness=0.85)
    alu = principled_material("Hub", (0.75, 0.77, 0.80, 1), metallic=1.0, roughness=0.25)
    glass = principled_material("LidarGlass", (0.02, 0.03, 0.04, 1), roughness=0.08)

    def part(obj, mat, parent=root):
        assign_material(obj, mat)
        obj.parent = parent
        return obj

    body = part(add_cube("Body", (0, 0, 0.135), (0.19, 0.155, 0.065), bevel=0.0), white)
    apply_bevel(body, 0.045, 6)
    part(add_cube("Bumper", (0, 0, 0.085), (0.197, 0.162, 0.018), bevel=0.012), dark)
    part(add_cube("Deck", (0, 0, 0.203), (0.15, 0.12, 0.004), bevel=0.003), dark)
    part(add_cylinder("LidarBase", (0.05, 0, 0.225), radius=0.05, depth=0.04, bevel=0.006), dark)
    part(add_cylinder("LidarWindow", (0.05, 0, 0.252), radius=0.047, depth=0.016, bevel=0.0), glass)
    part(add_cylinder("LidarCap", (0.05, 0, 0.266), radius=0.05, depth=0.012, bevel=0.004), dark)
    part(add_cube("LED", (0.199, 0, 0.15), (0.004, 0.10, 0.006), bevel=0.002),
         create_emission_material("StatusLED", (0.10, 0.75, 1.0, 1), 6.0))
    for x in (0.15, -0.15):
        part(add_sphere(f"Caster{x}", (x, 0, 0.022), 0.022), alu)
    wheels = []
    for side, name in ((1, "Left"), (-1, "Right")):
        pivot = bpy.data.objects.new(f"Wheel{name}", None)
        bpy.context.collection.objects.link(pivot)
        pivot.parent = root
        pivot.location = (0, side * 0.21, 0.10)
        tyre = add_cylinder(f"Tyre{name}", (0, 0, 0), radius=0.10, depth=0.05, bevel=0.012)
        tyre.rotation_euler = (math.pi / 2, 0, 0)
        part(tyre, rubber, pivot)
        hub = add_cylinder(f"Hub{name}", (0, side * 0.002, 0), radius=0.062, depth=0.052, bevel=0.004)
        hub.rotation_euler = (math.pi / 2, 0, 0)
        part(hub, alu, pivot)
        for k in range(3):
            spoke = add_cube(f"Spoke{name}{k}", (0, side * 0.027, 0), (0.055, 0.003, 0.008), bevel=0.002)
            spoke.rotation_euler = (0, k * math.pi / 3, 0)
            part(spoke, dark, pivot)
        wheels.append(pivot)
    return root, wheels, {"wheel_radius": 0.10, "wheel_separation": 0.42, "variant": "procedural"}


def diff_drive_wheel_angles(samples, wheel_radius, wheel_separation, time_key="t", cmd_key="cmd"):
    """Integrate (left, right) wheel angles for the *displayed* robot from commanded (v, w).

    Rolling without slip for the shown geometry; the planner's own model parameters may differ.
    """
    angles, left, right, last_t = [], 0.0, 0.0, None
    for s in samples:
        t = float(s[time_key])
        if last_t is not None:
            v, w = prev_cmd
            dt = t - last_t
            left += (v - w * wheel_separation / 2) / wheel_radius * dt
            right += (v + w * wheel_separation / 2) / wheel_radius * dt
        angles.append((left, right))
        last_t, prev_cmd = t, s[cmd_key]
    return angles


def set_robot(root, wheels, pose, wheel_angle, frame=None):
    root.location = (pose[0], pose[1], 0)
    root.rotation_euler = (0, 0, pose[2])
    for pivot, angle in zip(wheels, wheel_angle):
        pivot.rotation_euler = (0, angle, 0)
    if frame is not None:
        root.keyframe_insert("location", frame=frame)
        root.keyframe_insert("rotation_euler", frame=frame)
        for pivot in wheels:
            pivot.keyframe_insert("rotation_euler", frame=frame)


# ---------- glowing paths ----------
def build_band(points, z=0.035, dot_radius=0.034, line_radius=0.012, color=None, strength=1.6):
    mat = create_emission_material("Band", color or STUDIO["band"], strength)
    dots = [add_sphere(f"BandDot{i}", (x, y, z), dot_radius) for i, (x, y) in enumerate(points)]
    for d in dots:
        assign_material(d, mat)
    line = add_trajectory("BandLine", [(x, y, z) for x, y in points], mat, radius=line_radius)
    return dots, line


def key_band(dots, line, points, frame, z=0.035):
    for d, p, sp in zip(dots, points, line.data.splines[0].points):
        d.location = (p[0], p[1], z)
        d.keyframe_insert("location", frame=frame)
        sp.co = (p[0], p[1], z, 1)
        sp.keyframe_insert("co", frame=frame)


def reveal_trajectory(curve_obj, points, first_frame=1):
    """Grow a POLY curve so its tip sits exactly on points[i] at frame first_frame + i."""
    curve_obj.data.bevel_factor_mapping_end = "SPLINE"
    cum = [0.0]
    for a, b in zip(points, points[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    total = cum[-1] or 1.0
    for i, c in enumerate(cum):
        curve_obj.data.bevel_factor_end = c / total
        curve_obj.data.keyframe_insert("bevel_factor_end", frame=first_frame + i)
    set_interpolation(curve_obj.data, "LINEAR")
    return curve_obj


# ---------- camera ----------
def make_camera(dof_fstop=None):
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.sensor_width = SENSOR
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.clip_end = 200
    if dof_fstop:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = dof_fstop
    return cam


def look(cam, location, target, up_blend=0.0):
    """Orient -Z at target; up blends world Z -> world Y so a crane can end in a stable top view."""
    loc, tgt = Vector(location), Vector(target)
    f = (tgt - loc).normalized()
    up = (Vector((0, 0, 1)) * (1 - up_blend) + Vector((0, 1, 0)) * up_blend).normalized()
    r = f.cross(up)
    if r.length < 1e-6:
        r = Vector((1, 0, 0))
    r.normalize()
    m = Matrix((r, r.cross(f), -f)).transposed().to_4x4()
    m.translation = loc
    cam.matrix_world = m


def key_camera(cam, frame, location, target, lens, up_blend=0.0, focus=None):
    look(cam, location, target, up_blend)
    cam.data.lens = lens
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)
    cam.data.keyframe_insert("lens", frame=frame)
    if focus is not None:
        cam.data.dof.focus_distance = focus
        cam.data.dof.keyframe_insert("focus_distance", frame=frame)


def top_view(width_m, center=(0.0, 0.0), lens=100.0):
    """Camera location/target whose floor footprint is width_m wide: matches a 2D top-view window."""
    tgt = Vector((center[0], center[1], 0))
    return tgt + Vector((0, 0, width_m * lens / SENSOR)), tgt, lens


def crane_pose(start_loc, start_tgt, start_lens, end_loc, end_tgt, end_lens, s):
    """Pose at progress s in [0,1]: distance grows early, direction turns late, lens log-interpolated."""
    s = smoothstep(s)
    sd = 1 - (1 - s) ** 2
    tgt = start_tgt.lerp(end_tgt, s)
    d0, d1 = start_loc - start_tgt, end_loc - end_tgt
    dist = math.exp(math.log(d0.length) * (1 - sd) + math.log(d1.length) * sd)
    loc = end_loc if s >= 1 else tgt + d0.normalized().slerp(d1.normalized(), s) * dist
    lens = math.exp(math.log(start_lens) * (1 - s) + math.log(end_lens) * s)
    return loc, tgt, lens, s
