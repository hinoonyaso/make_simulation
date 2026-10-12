"""Run under Blender to exercise registry-checked collection import behavior."""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.education.blender_asset_loader import load_education_asset


def _clear_scene(scene):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(scene.collection.children):
        scene.collection.children.unlink(collection)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--report",type=Path,default=ROOT/"assets/education/generated/asset_loader_validation.json")
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    scene=bpy.context.scene; results=[]
    for asset_id in ("edu.bearing_6204.v1","edu.bldc_motor_concept.v1","edu.pcb_layered.v1"):
        _clear_scene(scene)
        imported=load_education_asset(asset_id,scene,location=(.4,-.2,.3),rotation=(0,0,.2),scale=(1.5,1.5,1.5),animation_mode="PLAY")
        if imported["root_object"].location != Vector((.4,-.2,.3)):
            raise RuntimeError(f"{asset_id}: assembly location was not applied")
        if not imported["objects"] or any(obj.name not in scene.objects for obj in imported["objects"]):
            raise RuntimeError(f"{asset_id}: collection import did not link all objects to the scene")
        hierarchy={obj.name:obj.parent.name if obj.parent else None for obj in imported["objects"]}
        _clear_scene(scene)
        frozen=load_education_asset(asset_id,scene,animation_mode="STATIC",animation_frame=36)
        if any(obj.animation_data for obj in frozen["objects"]):
            raise RuntimeError(f"{asset_id}: STATIC mode retained animated actions")
        override=bpy.data.materials.new(f"Loader override | {asset_id}")
        _clear_scene(scene)
        overlaid=load_education_asset(asset_id,scene,material_override=override)
        mesh_count=sum(obj.type=="MESH" for obj in overlaid["objects"])
        if any(not obj.data.materials or obj.data.materials[0] != override
               for obj in overlaid["objects"] if obj.type=="MESH"):
            raise RuntimeError(f"{asset_id}: material override did not reach every mesh")
        results.append({"asset_id":asset_id,"status":"PASS","source_sha256":overlaid["sha256"],
                        "license":overlaid["license"],"collection":overlaid["collection"],
                        "object_count":len(overlaid["objects"]),"mesh_count":mesh_count,
                        "hierarchy":hierarchy,"play_and_static_modes":"PASS","material_override":"PASS"})
    report={"blender_version":bpy.app.version_string,"assets":results,"status":"PASS"}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__": main()
