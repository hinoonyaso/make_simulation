"""Pilot Blender shots built on core/.../templates/studio_utils.py, driven only by data/*.json.

S1 (beat B01): TurtleBot3 at the band_trace what-if pose, initial band appears, camera cranes to
    the top view that the Manim shot (S2) continues from. Length = B01.sec from visual_manifest.json.
S3 (beat B07): full teb_obstacle drive from drive_trace.json; band refreshed every control step,
    executed trail revealed exactly under the robot. Length = B07.sec (drive + hold).

./render.sh S1 PREVIEW stills 1 120 240   |   ./render.sh S3 FINAL anim
"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "core/blender-robotics-simulation-skill/templates"))
import studio_utils as su  # noqa: E402
from animation_utils import set_interpolation  # noqa: E402
from robotics_visual_utils import add_trajectory, create_emission_material  # noqa: E402

FPS = su.FPS
TOP_WIDTH = 5.6  # must equal manim_shot.TOP_WIDTH
TOP_CENTER = (0.0, 0.0)


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def beat_frames(beat_id):
    beat = next(b for b in load("visual_manifest.json")["beats"] if b["id"] == beat_id)
    return round(float(beat["sec"]) * FPS)


def lerp(a, b, s):
    return [x + (y - x) * s for x, y in zip(a, b)]


def build_set(drive):
    su.add_studio_floor()
    su.add_corridor(drive["corridor_half_width"])
    su.add_drum(drive["obstacle"], drive["obstacle_radius"])
    su.add_floor_dashes(-3.0, 3.0)
    su.add_goal_ring(drive["goal"][:2])
    su.studio_lights()


def shot_s1(profile):
    band = load("data/band_trace.json")
    drive = load("data/drive_trace.json")
    frames = beat_frames("B01")
    su.setup_studio(profile, frames)
    build_set(drive)
    root, wheels, _ = su.load_turtlebot3()
    su.set_robot(root, wheels, band["pose"], (0.0, 0.0))
    dots, line = su.build_band([p[:2] for p in band["samples"][0]["poses"]])
    # Timeline as fractions of the narrated beat: hero push-in, band grows, crane, hold.
    f_band0, f_band1 = round(frames * 0.20), round(frames * 0.38)
    f_crane0, f_crane1 = round(frames * 0.50), round(frames * 0.93)
    step = (f_band1 - f_band0 - 8) / max(len(dots) - 1, 1)
    for i, d in enumerate(dots):
        start = round(f_band0 + i * step)
        d.scale = (0, 0, 0); d.keyframe_insert("scale", frame=start)
        d.scale = (1, 1, 1); d.keyframe_insert("scale", frame=start + 8)
    line.data.bevel_factor_end = 0.0
    line.data.keyframe_insert("bevel_factor_end", frame=f_band0)
    line.data.bevel_factor_end = 1.0
    line.data.keyframe_insert("bevel_factor_end", frame=f_band1)
    cam = su.make_camera(dof_fstop=2.8)
    robot = Vector((band["pose"][0], band["pose"][1], 0.0))
    near_a, near_b = robot + Vector((-0.70, 0.66, 0.30)), robot + Vector((-0.66, 0.60, 0.36))
    tgt_a, tgt_b = robot + Vector((0.12, -0.03, 0.05)), robot + Vector((0.32, -0.05, 0.04))
    focus_pt = robot + Vector((-0.06, 0, 0.07))  # keep the robot sharp, let the drum fall off
    top_loc, top_tgt, top_lens = su.top_view(TOP_WIDTH, TOP_CENTER)
    for f in range(1, frames + 1):
        if f <= f_crane0:
            s = su.smoothstep((f - 1) / max(f_crane0 - 1, 1))
            loc, tgt, lens, up = near_a.lerp(near_b, s), tgt_a.lerp(tgt_b, s), 35.0, 0.0
        else:
            loc, tgt, lens, up = su.crane_pose(near_b, tgt_b, 35.0, top_loc, top_tgt, top_lens,
                                               (f - f_crane0) / (f_crane1 - f_crane0))
        su.key_camera(cam, f, loc, tgt, lens, up, focus=(loc - focus_pt).length)
    return frames


def shot_s3(profile):
    drive = load("data/drive_trace.json")
    samples = drive["samples"]
    frames = max(beat_frames("B07"), len(samples) + 15)
    su.setup_studio(profile, frames)
    build_set(drive)
    root, wheels, geo = su.load_turtlebot3()
    wheel_angles = su.diff_drive_wheel_angles(samples, geo["wheel_radius"], geo["wheel_separation"])
    dots, line = su.build_band(drive["bands"][0])
    trail_pts = [(s["pose"][0], s["pose"][1], 0.006) for s in samples]
    trail = add_trajectory("Trail", trail_pts, create_emission_material("Trail", su.STUDIO["trail"], 1.2), radius=0.012)
    su.reveal_trajectory(trail, trail_pts, first_frame=1)
    for f, (s, wa) in enumerate(zip(samples, wheel_angles), start=1):
        su.set_robot(root, wheels, s["pose"], wa, frame=f)
        if f == 1 or s["step"] != samples[f - 2]["step"]:
            su.key_band(dots, line, drive["bands"][s["step"]], f)
    hold = len(samples) + 1
    for d in dots:  # band fades out once the goal is reached
        d.scale = (1, 1, 1); d.keyframe_insert("scale", frame=hold)
        d.scale = (0, 0, 0); d.keyframe_insert("scale", frame=hold + 8)
    line.data.bevel_factor_end = 1.0
    line.data.keyframe_insert("bevel_factor_end", frame=hold)
    line.data.bevel_factor_end = 0.0
    line.data.keyframe_insert("bevel_factor_end", frame=hold + 8)
    for idb in (*dots, line.data):  # 5 Hz refreshes are discrete; the final fade eases
        set_interpolation(idb, "CONSTANT")
        set_interpolation(idb, "BEZIER", paths=("scale", "bevel_factor_end"))
    for idb in (root, *wheels):
        set_interpolation(idb, "LINEAR")
    cam = su.make_camera(dof_fstop=5.6)
    # Camera on the +y side (robot passes the drum on +y, so the drum never occludes it).
    xs = [s["pose"][0] for s in samples] + [samples[-1]["pose"][0]] * (frames - len(samples))
    win = 30
    for f in range(1, frames + 1):
        lo, hi = max(0, f - 1 - win), min(len(xs), f + win)
        cx = sum(xs[lo:hi]) / (hi - lo)
        s = su.smoothstep((f - 1) / (frames - 1))
        tgt = Vector((cx, 0.08, 0.06))
        loc = tgt + Vector(lerp((-1.05, 1.30, 0.78), (-0.68, 1.10, 0.50), s))
        rp = samples[min(f, len(samples)) - 1]["pose"]
        su.key_camera(cam, f, loc, tgt, lens=30.0 + 8.0 * s, focus=(loc - Vector((rp[0], rp[1], 0.08))).length)
    return frames


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    shot, profile, mode = argv[0], argv[1], argv[2]
    frames = {"S1": shot_s1, "S3": shot_s3}[shot](profile)
    out = HERE / "output" / "blender" / f"{shot}_{profile.lower()}"
    out.mkdir(parents=True, exist_ok=True)
    s = bpy.context.scene
    s.render.image_settings.file_format = "PNG"
    if mode == "stills":
        for f in [int(x) for x in argv[3:]] or [1, frames // 2, frames]:
            s.frame_set(f)
            s.render.filepath = str(out / f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        s.render.filepath = str(out / "frame_")
        bpy.ops.render.render(animation=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{shot}.blend"))
    print(f"DONE {shot} {profile} {mode} frames={frames}")


main()
