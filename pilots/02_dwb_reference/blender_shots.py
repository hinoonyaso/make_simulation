"""DWB reference pilot Blender shots; data comes from pilots/02_dwb_reference/data only."""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parents[1]
sys.path.insert(0, str(BUNDLE / "core/blender-robotics-simulation-skill/templates"))
import studio_utils as su  # noqa: E402
from animation_utils import set_interpolation  # noqa: E402
from robotics_visual_utils import add_trajectory, create_emission_material  # noqa: E402

FPS = su.FPS
TOP_WIDTH = 5.6
TOP_CENTER = (0.0, 0.0)


def load(name):
    return json.loads((HERE / "data" / name).read_text(encoding="utf-8"))


def beat_frames(beat_id):
    doc = json.loads((HERE / "visual_manifest.json").read_text(encoding="utf-8"))
    beat = next(b for b in doc["beats"] if b["id"] == beat_id)
    return round(float(beat["sec"]) * FPS)


def build_set(data):
    su.add_studio_floor()
    su.add_corridor(data["corridor_half_width"])
    su.add_drum(data["obstacle"], data["obstacle_radius"])
    su.add_floor_dashes(-3.0, 3.0)
    su.add_goal_ring(data.get("goal", [3.0, 0.0])[:2])
    su.studio_lights()


def hero(profile):
    data = load("candidate_trace.json")
    frames = beat_frames("B01")
    su.setup_studio(profile, frames)
    build_set(data)
    root, wheels, _ = su.load_turtlebot3()
    su.set_robot(root, wheels, data["pose"], (0.0, 0.0))

    cam = su.make_camera(dof_fstop=3.2)
    robot = Vector((data["pose"][0], data["pose"][1], 0.0))
    near_a = robot + Vector((-0.80, 0.82, 0.52))
    near_b = robot + Vector((-0.67, 0.66, 0.42))
    tgt_a = robot + Vector((0.04, -0.04, 0.12))
    tgt_b = robot + Vector((0.22, -0.02, 0.05))
    top_loc, top_tgt, top_lens = su.top_view(TOP_WIDTH, TOP_CENTER)
    crane_start = round(frames * 0.48)
    crane_end = round(frames * 0.92)
    focus_pt = robot + Vector((-0.04, 0.0, 0.10))
    for f in range(1, frames + 1):
        if f <= crane_start:
            s = su.smoothstep((f - 1) / max(crane_start - 1, 1))
            loc, target, lens, up = near_a.lerp(near_b, s), tgt_a.lerp(tgt_b, s), 35.0, 0.0
        else:
            loc, target, lens, up = su.crane_pose(
                near_b, tgt_b, 35.0, top_loc, top_tgt, top_lens,
                (f - crane_start) / max(crane_end - crane_start, 1),
            )
        su.key_camera(cam, f, loc, target, lens, up, focus=(loc - focus_pt).length)
    return frames


def drive(profile):
    data = load("drive_trace.json")
    samples = data["samples"]
    decisions = data["decisions"]
    frames = max(beat_frames("B07"), len(samples))
    su.setup_studio(profile, frames)
    build_set(data)
    root, wheels, geo = su.load_turtlebot3()
    angles = su.diff_drive_wheel_angles(samples, geo["wheel_radius"], geo["wheel_separation"])
    trail_pts = [(s["pose"][0], s["pose"][1], 0.008) for s in samples]
    trail = add_trajectory("ExecutedTrail", trail_pts,
                           create_emission_material("ExecutedTrail", su.STUDIO["trail"], 1.4), radius=0.013)
    su.reveal_trajectory(trail, trail_pts, first_frame=1)

    first = decisions[0]
    dots, prediction = su.build_band([p[:2] for p in first["prediction"]],
                                     color=su.STUDIO["band"], strength=1.25)
    sample_by_step = {s["step"]: s for s in decisions}
    for f, (sample, wheel) in enumerate(zip(samples, angles), start=1):
        su.set_robot(root, wheels, sample["pose"], wheel, frame=f)
        if f == 1 or sample["step"] != samples[f - 2]["step"]:
            choice = sample_by_step.get(sample["step"])
            if choice and choice["selected"] >= 0:
                su.key_band(dots, prediction, [p[:2] for p in choice["prediction"]], f)
                for dot in dots:
                    dot.scale = (1, 1, 1)
                    dot.keyframe_insert("scale", frame=f)
            else:
                for dot in dots:
                    dot.scale = (0, 0, 0)
                    dot.keyframe_insert("scale", frame=f)
                prediction.data.bevel_factor_end = 0.0
                prediction.data.keyframe_insert("bevel_factor_end", frame=f)
    for obj in (root, *wheels):
        set_interpolation(obj, "LINEAR")
    for obj in (*dots, prediction.data):
        set_interpolation(obj, "CONSTANT")

    cam = su.make_camera(dof_fstop=5.6)
    xs = [s["pose"][0] for s in samples]
    for f in range(1, frames + 1):
        i = min(f - 1, len(samples) - 1)
        pose = samples[i]["pose"]
        target = Vector((pose[0], 0.08, 0.05))
        # Slightly high 3/4 view, matching the pilot's route composition.
        loc = target + Vector((-0.78, 1.20, 0.70))
        su.key_camera(cam, f, loc, target, lens=37.0, focus=(loc - Vector((pose[0], pose[1], 0.10))).length)
    return frames


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    shot, profile, mode = args[0], args[1], args[2]
    frames = {"S1": hero, "S3": drive}[shot](profile)
    out = HERE / "output" / "blender" / f"{shot}_{profile.lower()}"
    out.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    if mode == "stills":
        for f in [int(x) for x in args[3:]] or [1, frames // 2, frames]:
            scene.frame_set(f)
            scene.render.filepath = str(out / f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        scene.render.filepath = str(out / "frame_")
        bpy.ops.render.render(animation=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{shot}.blend"))
    print(f"DONE {shot} {profile} {mode} frames={frames}")


main()
