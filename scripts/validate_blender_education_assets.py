"""Open generated education .blend assets in the active Blender process and inspect them."""
import json
import hashlib
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/education/generated"


def _assert_close(label, actual, expected, tol=1e-5):
    if abs(actual - expected) > tol:
        raise RuntimeError(f"{label}: expected {expected:.8g}, got {actual:.8g}")


def _kinematic_checks(scene, filename):
    frames = (1, 36, 72)
    if filename == "spur_gears_20_40.blend":
        pinion, gear = scene.objects["Pinion_20T"], scene.objects["Gear_40T"]
        samples = {obj.name: [] for obj in (pinion, gear)}
        for frame in frames:
            scene.frame_set(frame)
            for obj in (pinion, gear):
                samples[obj.name].append((tuple(obj.matrix_world.translation), obj.rotation_euler.z))
        for obj in (pinion, gear):
            origin = samples[obj.name][0][0]
            if any((Vector(location) - Vector(origin)).length > 1e-6 for location, _ in samples[obj.name]):
                raise RuntimeError(f"gear center moved during rotation: {obj.name}")
        start1, middle1, end1 = (row[1] for row in samples[pinion.name])
        start2, middle2, end2 = (row[1] for row in samples[gear.name])
        _assert_close("20T angular ratio", (middle1-start1)/(middle2-start2), -2.0, 1e-4)
        if middle1 <= start1 or middle2 >= start2 or end1 <= middle1 or end2 >= middle2:
            raise RuntimeError("gear rotations must be continuous and opposite")
        _assert_close("gear center distance", (Vector(samples[gear.name][0][0])-Vector(samples[pinion.name][0][0])).length, .06, 1e-6)
        return {"status":"PASS", "frames":list(frames), "gear_center_distance_m":.06,
                "center_drift_m":0, "angular_ratio_20_to_40":-2.0,
                "profile_note":"polygonal non-involute; mesh contact fidelity is not claimed"}
    if filename == "bldc_motor_concept.blend":
        assembly, root, rotor, magnet = (scene.objects[n] for n in ("BLDC_Assembly","Rotor_Assembly","Rotor_Core","Rotor_Magnet_01"))
        stator_root, stator = scene.objects["Stator_Assembly"], scene.objects["Stator_Core"]
        if root.parent != assembly or stator_root.parent != assembly:
            raise RuntimeError("BLDC_Assembly must contain Rotor_Assembly and Stator_Assembly")
        if rotor.parent != root or magnet.parent != root or scene.objects["Motor_Shaft"].parent != root:
            raise RuntimeError("rotor, magnets and shaft must share Rotor_Assembly")
        if stator.parent != stator_root or scene.objects["Stator_Tooth_01"].parent != stator_root or \
                scene.objects["Phase_A_Coil_01"].parent != stator_root:
            raise RuntimeError("stator core, teeth and coils must share Stator_Assembly")
        bore_radius=.038; core_radius=.020
        magnet_radii=[math.hypot((magnet.matrix_world @ Vector(corner)).x,
                                 (magnet.matrix_world @ Vector(corner)).y) for corner in magnet.bound_box]
        if max(magnet_radii) <= core_radius+.01 or max(magnet_radii) >= bore_radius:
            raise RuntimeError("BLDC pole magnets must be exposed beyond the rotor core and inside the stator bore")
        coil=scene.objects["Phase_A_Coil_01"]
        states=[]
        for frame in frames:
            scene.frame_set(frame)
            states.append((tuple(rotor.matrix_world.translation), tuple(magnet.matrix_world.translation), tuple(stator.matrix_world.translation), root.rotation_euler.z, tuple(coil.matrix_world.translation)))
        magnet_motion=(Vector(states[0][1])-Vector(states[1][1])).length
        if magnet_motion < .02:
            raise RuntimeError("rotor magnet did not orbit with rotor assembly")
        if any((Vector(s[0])-Vector(states[0][0])).length > 1e-6 for s in states):
            raise RuntimeError("rotor core center moved")
        if any((Vector(s[2])-Vector(states[0][2])).length > 1e-6 for s in states):
            raise RuntimeError("stator moved with rotor")
        if any((Vector(s[4])-Vector(states[0][4])).length > 1e-6 for s in states):
            raise RuntimeError("stator phase coil moved with rotor")
        expected_angle=math.tau*(frames[1]-frames[0])/(frames[-1]-frames[0])
        _assert_close("Rotor_Assembly middle-frame angle", states[1][3], expected_angle, 2e-4)
        return {"status":"PASS", "frames":list(frames), "rotor_magnet_midframe_displacement_m":magnet_motion,
                "magnet_radial_extent_m":[min(magnet_radii),max(magnet_radii)],
                "stator_drift_m":0, "hierarchy":"BLDC_Assembly -> Rotor_Assembly and Stator_Assembly"}
    if filename == "beam_bracket_heatsink_fan.blend":
        assembly, root, hub, blade, frame_obj = (scene.objects[n] for n in ("Cooling_Fan","Fan_Rotor","Fan_Hub","Fan_Blade_1","Fan_Frame"))
        if root.parent != assembly or frame_obj.parent != assembly or hub.parent != root or blade.parent != root:
            raise RuntimeError("Cooling_Fan must contain a fixed frame and animated Fan_Rotor with hub/blades")
        states=[]
        for frame in frames:
            scene.frame_set(frame)
            states.append((tuple(hub.matrix_world.translation),tuple(blade.matrix_world.translation),tuple(frame_obj.matrix_world.translation),root.rotation_euler.y))
        if (Vector(states[0][1])-Vector(states[1][1])).length < .005:
            raise RuntimeError("fan blade did not rotate around hub")
        if any((Vector(s[2])-Vector(states[0][2])).length > 1e-6 for s in states):
            raise RuntimeError("fan frame moved")
        radii=[(Vector(s[1])-Vector(s[0])).length for s in states]
        if max(radii)-min(radii)>1e-6:
            raise RuntimeError("fan blade radial position changed")
        expected_angle=math.tau*(frames[1]-frames[0])/(frames[-1]-frames[0])
        _assert_close("Fan_Rotor middle-frame angle", states[1][3], expected_angle, 2e-4)
        return {"status":"PASS", "frames":list(frames), "blade_orbit_radius_m":radii[0],
                "frame_drift_m":0, "hierarchy":"Cooling_Fan -> fixed Fan_Frame and Fan_Rotor -> hub/blades"}
    if filename == "bearing_6204.blend":
        outer, inner, cage, ball = (scene.objects[n] for n in ("Outer_Ring","Inner_Ring","Cage_Assembly","Ball_01"))
        meta=json.loads((OUT/"bearing_6204.json").read_text(encoding="utf-8"))
        motion=meta["motion"]
        positions=[]; cage_angles=[]
        for frame in frames:
            scene.frame_set(frame)
            positions.append(tuple(ball.matrix_world.translation))
            cage_angles.append(cage.rotation_euler.z)
            if (outer.location.length>1e-7 or inner.location.length>1e-7):
                raise RuntimeError("bearing race centers must remain fixed")
        if abs(outer.rotation_euler.z)>1e-7 or abs(inner.rotation_euler.z)<1e-4:
            raise RuntimeError("bearing outer race must be fixed and inner race must rotate")
        pitch=motion["inner_contact_radius_m"] + motion["ball_radius_m"]
        radii=[math.hypot(p[0],p[1]) for p in positions]
        if max(abs(r-pitch) for r in radii)>2e-5:
            raise RuntimeError("bearing ball center does not stay on declared pitch circle")
        expected=2*math.pi*(35/71)*motion["cage_angular_speed_over_inner"]
        _assert_close("bearing cage speed ratio", cage_angles[1], expected, 2e-4)
        return {"status":"PASS", "frames":list(frames), "outer_fixed":True, "inner_center_fixed":True,
                "ball_pitch_radius_m":pitch, "cage_midframe_rad":cage_angles[1],
                "ideal_no_slip_prescribed_motion":True, "contact_solver":False}
    return None


def main():
    report = json.loads((OUT / "generation_report.json").read_text(encoding="utf-8"))
    results = []
    for row in report:
        path = OUT / row["blend_file"]
        if not path.is_file() or path.stat().st_size < 1024:
            raise RuntimeError(f"missing or too-small Blender asset: {path}")
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        sidecar=json.loads((OUT/(path.stem+".json")).read_text(encoding="utf-8"))
        if sidecar.get("source_sha256") != digest:
            raise RuntimeError(f"sidecar source hash mismatch: {path.name}")
        bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
        scene = bpy.context.scene
        objects = [obj for obj in scene.objects if obj.type in {"MESH", "CURVE", "EMPTY"}]
        if not objects:
            raise RuntimeError(f"no model objects in {path.name}")
        if scene.unit_settings.system != "METRIC" or abs(scene.unit_settings.scale_length - 1.0) > 1e-9:
            raise RuntimeError(f"unit mismatch in {path.name}")
        bounds = [tuple(obj.dimensions) for obj in objects if obj.type == "MESH"]
        if not bounds or not any(all(v > 0 for v in d) for d in bounds):
            raise RuntimeError(f"no nonzero mesh dimensions in {path.name}")
        keyed = [obj.name for obj in objects if obj.animation_data and obj.animation_data.action]
        if row["animation_ready"] != bool(keyed):
            raise RuntimeError(f"animation metadata mismatch in {path.name}: {keyed}")
        kinematics=_kinematic_checks(scene,path.name)
        results.append({"file": path.name, "size_bytes": path.stat().st_size,
                        "scene": scene.name, "sha256": digest, "units": "m", "object_count": len(objects),
                        "mesh_object_count": sum(obj.type == "MESH" for obj in objects),
                        "keyframed_object_count": len(keyed),
                        "bounds_m": [[min(d[i] for d in bounds), max(d[i] for d in bounds)] for i in range(3)],
                        "kinematics":kinematics,"validation": "PASS"})
    payload = {"blender_version": bpy.app.version_string, "assets": results,
               "preview_pngs": [p.name for p in sorted(OUT.glob("*.png"))],
               "all_previews_present": all((OUT / f"{row['scene']}.png").is_file() for row in report)}
    if not payload["all_previews_present"]:
        raise RuntimeError("one or more expected PNG previews are missing")
    (OUT / "blender_validation.json").write_bytes((json.dumps(payload, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
