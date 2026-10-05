"""Single continuous, trace-driven moving-obstacle scene. Uses the shared studio kit."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "core/blender-robotics-simulation-skill/templates"))
import studio_utils as su  # noqa: E402
from animation_utils import set_interpolation  # noqa: E402
from geometry_utils import add_cube  # noqa: E402
from material_utils import assign_material, principled_material  # noqa: E402
from robotics_visual_utils import add_trajectory, create_emission_material  # noqa: E402

FPS = 30
TOTAL_SEC = 86.0
FRAMES = round(TOTAL_SEC * FPS)
TRACE = json.loads((HERE / "data/trace.json").read_text(encoding="utf-8"))
BEATS = json.loads((HERE / "visual_manifest.json").read_text(encoding="utf-8"))["beats"]
EDGES = [0.0]
for _beat in BEATS: EDGES.append(EDGES[-1] + float(_beat["sec"]))


def mat(name, color, strength=0.0):
    if strength:
        return create_emission_material(name, color, strength)
    return principled_material(name, color, roughness=0.65)


def frame_for(sec):
    return max(1, min(FRAMES, round(float(sec) * FPS)))


def add_source_room():
    su.add_studio_floor()
    su.studio_lights()
    wall = mat("RoomEdge", (0.79, 0.81, 0.83, 1))
    trim = mat("RoomTrim", (0.22, 0.24, 0.27, 1))
    for name, loc, scale in (
        ("NorthWall", (0, 3.02, .18), (4.5, .035, .18)),
        ("SouthWall", (0, -3.02, .18), (4.5, .035, .18)),
        ("WestWall", (-4.52, 0, .18), (.035, 3, .18)),
        ("EastWall", (4.52, 0, .18), (.035, 3, .18)),
    ):
        o = add_cube(name, loc, scale, bevel=.012); assign_material(o, wall)
    for i, (x0, y0, x1, y1) in enumerate(TRACE["boxes"]):
        o = add_cube(f"SourceBox{i+1}", ((x0+x1)/2, (y0+y1)/2, .16),
                     ((x1-x0)/2, (y1-y0)/2, .16), bevel=.035)
        assign_material(o, trim)
    su.add_goal_ring(TRACE["goal"][:2], radius=.18)


_HEAT_MATERIALS = {}


def heat_material(value):
    # Source cost values are binned only for display; cell placement and costs come from model.costmap.
    key = 255 if value >= 255 else 100 if value >= 100 else 40 if value >= 40 else 1 if value >= 1 else 0
    if key in _HEAT_MATERIALS: return _HEAT_MATERIALS[key]
    if key == 255: result = mat("CostForbidden", (.76, .12, .13, 1), .7)
    elif key == 100: result = mat("CostHigh", (1.0, .36, .12, 1), .55)
    elif key == 40: result = mat("CostMid", (1.0, .67, .25, 1), .42)
    elif key == 1: result = mat("CostLow", (1.0, .88, .56, 1), .26)
    else: result = None
    _HEAT_MATERIALS[key] = result
    return result


def add_costmap(snapshot, name):
    xs, ys, values = TRACE["xs"], TRACE["ys"], snapshot["cost"]
    verts, faces, face_levels = [], [], []
    for j in range(len(ys)-1):
        for i in range(len(xs)-1):
            value = max(values[j][i], values[j][i+1], values[j+1][i], values[j+1][i+1])
            if value <= 0: continue
            base = len(verts)
            z = .006 + min(value, 255) / 255 * .012
            verts.extend(((xs[i],ys[j],z),(xs[i+1],ys[j],z),(xs[i+1],ys[j+1],z),(xs[i],ys[j+1],z)))
            faces.append((base,base+1,base+2,base+3))
            face_levels.append(255 if value >= 255 else 100 if value >= 100 else 40 if value >= 40 else 1)
    mesh = bpy.data.meshes.new(name+"Mesh"); mesh.from_pydata(verts, [], faces); mesh.update()
    obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
    bins = (1,40,100,255)
    for b in bins:
        m = heat_material(b); mesh.materials.append(m)
    for poly, level in zip(mesh.polygons, face_levels):
        poly.material_index = bins.index(level)
    obj.hide_render = True; obj.hide_viewport = True
    map_t2 = EDGES[3]
    map_t3 = EDGES[4] + 7.0
    for f in (1, frame_for(map_t2), frame_for(map_t3), FRAMES):
        active = (name == "Costmap_t0" and f < frame_for(map_t2)) or \
                 (name == "Costmap_t2" and frame_for(map_t2) <= f < frame_for(map_t3)) or \
                 (name == "Costmap_t3" and f >= frame_for(map_t3))
        obj.hide_render = not active; obj.keyframe_insert("hide_render", frame=f)
        obj.hide_viewport = not active; obj.keyframe_insert("hide_viewport", frame=f)
    return obj


def path_curve(name, pts, color, bevel=.018):
    points = [(float(p[0]), float(p[1]), .034) for p in pts]
    if len(points) < 2: return None
    curve = add_trajectory(name, points, mat(name+"Glow", color, 1.1), radius=bevel)
    curve.data.bevel_factor_end = 1.0
    curve.data.keyframe_insert("bevel_factor_end", frame=1)
    curve.data.bevel_factor_end = 0.0
    curve.data.keyframe_insert("bevel_factor_end", frame=frame_for(11))
    curve.data.bevel_factor_end = 1.0
    curve.data.keyframe_insert("bevel_factor_end", frame=frame_for(23))
    curve.data.bevel_factor_end = 1.0
    curve.data.keyframe_insert("bevel_factor_end", frame=frame_for(37))
    return curve


def visibility(obj, start, stop):
    for sec, hidden in ((1/FPS, True), (start, True), (start+.05, False), (stop, False), (stop+.05, True), (TOTAL_SEC, True)):
        f = frame_for(sec)
        obj.hide_render = hidden; obj.keyframe_insert("hide_render", frame=f)
        obj.hide_viewport = hidden; obj.keyframe_insert("hide_viewport", frame=f)


def main(mode):
    su.setup_studio("PREVIEW" if mode == "preview" else "FINAL", FRAMES)
    add_source_room()
    # Costmap snapshots are the output of the source model's exact costmap(det) function.
    for snap, name in zip(TRACE["snapshots"], ("Costmap_t0", "Costmap_t2", "Costmap_t3")):
        add_costmap(snap, name)
    root, wheels, _ = su.load_turtlebot3()
    root.location = (TRACE["start"][0], TRACE["start"][1], 0)
    before_drum = set(bpy.context.scene.objects)
    obstacle = su.add_drum((0, .4), TRACE["circular_obstacle_radius_m"], height=.58)
    # Move all kit-created drum geometry together, including its two torus bands.
    drum_parts = [o for o in bpy.context.scene.objects if o not in before_drum]
    for obj in drum_parts:
        obj.location.x, obj.location.y = 0, 1.2
        obj.keyframe_insert("location", frame=frame_for(EDGES[2]))
        for t, pos in ((EDGES[2], (0,1.2)), (EDGES[3], (0,.4)), (EDGES[3]+10, (0,0))):
            obj.location.x, obj.location.y = pos
            obj.keyframe_insert("location", frame=frame_for(t))
        obj.location.x, obj.location.y = 0, 0
        obj.keyframe_insert("location", frame=FRAMES)

    # Direct path and successive source plans; preserve the previous line as it changes.
    snapshots = TRACE["snapshots"]
    old = path_curve("InitialPlan", snapshots[0]["path"], (.14,.35,.92,1), .022)
    invalid = add_trajectory("InvalidatedPlan",
                             [(p[0],p[1],.045) for p in snapshots[0]["path"]],
                             mat("InvalidatedPlanGlow", (.88,.08,.12,1), 1.15), radius=.024)
    reroute_a = add_trajectory("PlanBelow", [(p[0],p[1],.04) for p in snapshots[1]["path"]],
                               mat("PlanBelowGlow", (.05,.67,.30,1), 1.25), radius=.024)
    reroute_b = add_trajectory("PlanAbove", [(p[0],p[1],.046) for p in snapshots[2]["path"]],
                               mat("PlanAboveGlow", (.06,.56,.30,1), 1.25), radius=.024)
    route_b_start = EDGES[4] + 7.0
    for obj, start, finish in ((old,EDGES[1],EDGES[3]),
                               (invalid,EDGES[3],EDGES[4]),
                               (reroute_a,EDGES[4],route_b_start),
                               (reroute_b,route_b_start,EDGES[5])):
        obj.data.bevel_factor_end = 0; obj.data.keyframe_insert("bevel_factor_end", frame=frame_for(start))
        obj.data.bevel_factor_end = 1; obj.data.keyframe_insert("bevel_factor_end", frame=frame_for(finish))
    visibility(old, EDGES[1], EDGES[3])
    visibility(invalid, EDGES[3], EDGES[4])
    visibility(reroute_a, EDGES[4], route_b_start)
    visibility(reroute_b, route_b_start, EDGES[6])
    # Robot playback derives from source poses. Compress source time uniformly into the drive beat.
    playback = TRACE["playback"]
    wheels_geo = su.diff_drive_wheel_angles(playback, .033, .288, time_key="time")
    def scene_time(source_time):
        if source_time <= 2.0: return EDGES[2] + (source_time/2.0)*(EDGES[3]-EDGES[2])
        if source_time <= 3.0: return EDGES[3] + (source_time-2.0)*(EDGES[4]-EDGES[3])
        return EDGES[4] + (source_time-3.0)/14.2*(EDGES[6]-EDGES[4])
    for row, angle in zip(playback, wheels_geo):
        sec = scene_time(row["time"])
        su.set_robot(root, wheels, row["pose"], angle, frame=frame_for(sec))
    for obj in (root, *wheels): set_interpolation(obj, "LINEAR")

    # One unbroken crane from studio three-quarter view to a legible map overview.
    cam = su.make_camera(dof_fstop=5.0)
    low_a = Vector((-5.2,-7.4,5.6)); low_b = Vector((-4.3,-5.9,4.0))
    high = Vector((-.1,-.8,10.5)); target = Vector((0,0,0))
    for f in range(1, FRAMES+1):
        t = (f-1)/(FRAMES-1)
        if t < .32:
            k = su.smoothstep(t/.32); loc=low_a.lerp(low_b,k); lens=43
        else:
            k = su.smoothstep((t-.32)/.68); loc=low_b.lerp(high,k); lens=43+12*k
        look = target + Vector((.16*math.sin(t*math.pi),0,0))
        su.key_camera(cam,f,loc,look,lens,0,focus=(loc-look).length)
    scene = bpy.context.scene
    out = HERE / "output" / "blender"; out.mkdir(parents=True,exist_ok=True)
    if mode == "stills":
        scene.render.image_settings.file_format="PNG"
        for sec in (3,18,29,43,57,72,81):
            scene.frame_set(frame_for(sec)); scene.render.filepath=str(out/f"still_{sec:02d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        scene.eevee.taa_render_samples = 32
        frame_dir = HERE / "output/frames"; frame_dir.mkdir(parents=True, exist_ok=True)
        scene.render.image_settings.file_format="PNG"
        scene.render.image_settings.color_mode="RGB"
        scene.render.image_settings.compression=15
        scene.render.filepath=str(frame_dir / "frame_")
        bpy.ops.render.render(animation=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"moving_obstacle.blend"))
    print(f"DONE {mode} {FRAMES} frames {TOTAL_SEC}s")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    main(args[0] if args else "preview")
