"""Blender-side exporter used through AssetFactory's content-addressed cache."""
import argparse
import sys
from pathlib import Path
import bpy


def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type in {"MESH","CURVE","EMPTY"}:
            obj.select_set(True)
    result=bpy.ops.export_scene.gltf(filepath=str(args.output),export_format="GLB",
                                    use_selection=True,export_animations=True)
    if "FINISHED" not in result or not args.output.is_file() or args.output.stat().st_size < 20:
        raise RuntimeError("Blender GLB export did not produce a valid file")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    imported=bpy.ops.import_scene.gltf(filepath=str(args.output))
    mesh_count=sum(obj.type=="MESH" for obj in bpy.context.scene.objects)
    if "FINISHED" not in imported or mesh_count==0:
        raise RuntimeError("exported GLB did not re-import with mesh objects")


if __name__=="__main__":
    main()
