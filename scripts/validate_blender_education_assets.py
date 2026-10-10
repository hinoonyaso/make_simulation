"""Open generated education .blend assets in the active Blender process and inspect them."""
import json
import hashlib
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/education/generated"


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
        results.append({"file": path.name, "size_bytes": path.stat().st_size,
                        "scene": scene.name, "sha256": digest, "units": "m", "object_count": len(objects),
                        "mesh_object_count": sum(obj.type == "MESH" for obj in objects),
                        "keyframed_object_count": len(keyed),
                        "bounds_m": [[min(d[i] for d in bounds), max(d[i] for d in bounds)] for i in range(3)],
                        "validation": "PASS"})
    payload = {"blender_version": bpy.app.version_string, "assets": results,
               "preview_pngs": [p.name for p in sorted(OUT.glob("*.png"))],
               "all_previews_present": all((OUT / f"{row['scene']}.png").is_file() for row in report)}
    if not payload["all_previews_present"]:
        raise RuntimeError("one or more expected PNG previews are missing")
    (OUT / "blender_validation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
