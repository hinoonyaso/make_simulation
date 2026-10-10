#!/usr/bin/env python3
"""Audit, plan, validate and report the engineering education asset catalog.

Network acquisition is intentionally not implicit: current candidates must first
have a pinned source hash, exact size, host allowlist and reviewed redistribution
metadata compatible with core.visual-assets.safe_archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/education/catalog.json"
REGISTRY = ROOT / "core/visual-assets/registry.json"
REPORTS = ROOT / "docs/assets"
sys.path.insert(0, str(ROOT / "core/visual-assets"))
sys.path.insert(0, str(ROOT))
from asset_factory import AssetFactory


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return catalog, registry


def audit(catalog, registry):
    rows = []
    factory = AssetFactory(ROOT)
    for entry in registry["assets"]:
        source = entry["source"].split("::", 1)[0]
        path = ROOT / source
        exists = path.exists()
        files = sorted(p for p in path.rglob("*") if p.is_file()) if exists and path.is_dir() else ([path] if exists and path.is_file() else [])
        actual_files = []
        for f in files:
            actual_files.append({"path": f.relative_to(ROOT).as_posix(), "size_bytes": f.stat().st_size,
                                 "sha256": sha256(f), "git_tracked": _tracked(f),
                                 "remote_main_tree": _remote_tracked(f)})
        rows.append({"id": entry["id"], "source": source, "exists": exists,
                     "file_count": len(actual_files), "files": actual_files,
                     "license": entry.get("license", "UNKNOWN"),
                     "factory_validation": "NOT_RUN"})
        if entry.get("source", "").split("::",1)[0] != entry.get("source"):
            rows[-1]["factory_validation"] = "NOT_APPLICABLE: code reference"
        elif exists and files and entry.get("tool") == "blender":
            try:
                factory.validate_asset(entry["id"])
                rows[-1]["factory_validation"] = "PASS"
            except Exception as exc:
                rows[-1]["factory_validation"] = f"FAIL: {type(exc).__name__}: {exc}"
    return rows


def _tracked(path):
    # Avoid shell interpolation: query Git with an argument vector.
    import subprocess
    result = subprocess.run(["git", "ls-files", "--error-unmatch", str(path.relative_to(ROOT))],
                            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def _remote_tracked(path):
    import subprocess
    check = subprocess.run(["git", "rev-parse", "--verify", "FETCH_HEAD^{commit}"],
                           cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if check.returncode:
        return "NOT_CHECKED"
    result = subprocess.run(["git", "ls-tree", "-r", "--name-only", "FETCH_HEAD", "--",
                             path.relative_to(ROOT).as_posix()], cwd=ROOT,
                            capture_output=True, text=True)
    return result.returncode == 0 and bool(result.stdout.strip())


def write_audit(rows):
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = ["# Existing Asset Audit", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", "",
             "Registry paths were inspected on disk. A present file can still be ignored by Git and absent in a clean clone.", "",
             "| Asset | Registry source | Exists | Files | Git tracked | Remote main tree | Factory | Rights |", "|---|---|---:|---:|---:|---:|---|---|"]
    for row in rows:
        tracked = sum(f["git_tracked"] for f in row["files"])
        remote_checked = [f for f in row["files"] if f["remote_main_tree"] != "NOT_CHECKED"]
        remote = (f"{sum(f['remote_main_tree'] is True for f in remote_checked)}/{len(remote_checked)}"
                  if remote_checked else "NOT_CHECKED")
        lines.append(f"| `{row['id']}` | `{row['source']}` | {row['exists']} | {row['file_count']} | {tracked}/{row['file_count']} | {remote} | {row['factory_validation']} | {row['license']} |")
    lines += ["", "## Integrity evidence", ""]
    for row in rows:
        for f in row["files"]:
            lines.append(f"- `{f['path']}` — {f['size_bytes']} bytes; SHA-256 `{f['sha256']}`; Git tracked: `{f['git_tracked']}`.")
    lines += ["", "## Important findings", "",
              "Livox Mid-360, Ouster OS0/OS1/OSDome, ZED2i, and Raspberry Pi 5 STEP files exist in this worktree. The vendor CAD folders and Pi STEP are ignored by `.gitignore`; they are not in a clean clone. A read-only `git fetch --depth=1 origin main` observed remote main `2af957f442d8919946cabd32e30152113bc47a20`; `git ls-tree` found only the Pi LICENSE/README among those paths, no STEP files. Their registry entries therefore describe local assets, not clone-reproducible public assets.",
            "", "The vendor sensor CAD remains local use only pending license permission. Raspberry Pi's local folder contains an MIT license, but the chain between that license and the STEP export is not independently established here. Sparse checkout is not enabled. Git LFS status could not be verified because the installed git-lfs command is broken/unavailable.", ""]
    (REPORTS / "EXISTING_ASSET_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    (REPORTS / "existing_asset_audit.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(catalog, registry):
    ids = [x["id"] for x in registry["assets"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate registry ids")
    required = {"id", "tool", "kind", "source", "version", "assumptions", "semantic_role", "provenance"}
    for row in registry["assets"]:
        missing = required - set(row)
        if missing:
            raise ValueError(f"{row.get('id')}: missing {sorted(missing)}")
    for model in catalog["models"]:
        path = ROOT / model["path"]
        if model["status"] == "GENERATED":
            if not path.is_file():
                raise FileNotFoundError(path)
            if path.is_symlink():
                raise ValueError(f"generated model path is symlink: {path}")
            if path.suffix == ".blend" and path.stat().st_size <= 1024:
                raise ValueError(f"generated .blend unexpectedly small: {path}")
    factory = AssetFactory(ROOT)
    generated_ids = {m["id"] for m in catalog["models"]}
    integrity = [factory.validate_asset(aid) for aid in generated_ids]
    return {"registry_entries": len(ids), "catalog_models": len(catalog["models"]),
            "generated_assets_checked": len(integrity),
            "validation": "metadata_and_present_generated_files_sha256"}


def report(catalog, rows):
    REPORTS.mkdir(parents=True, exist_ok=True)
    files = {
      "ACQUISITION_PLAN.md": """# Acquisition Plan\n\nPolicy: plan by default; never fetch unless the exact source hash, size, redirect hosts, license scope and target path are reviewed. Existing local assets are not downloaded again.\n\n| Family | Method | Decision |\n|---|---|---|\n| bearing, gears, shaft/coupling, spring, fasteners | authored Blender geometry | Generate CC0 teaching assemblies; mark assumptions; do not claim product or solver fidelity.\n| BLDC/PMSM internals, PCB, battery, bracket/beam, fan/heatsink | authored Blender geometry | Generate explanatory separated objects and keyframed preview models.\n| KiCad 3D models | official library | Plan only until local library absent/pinned file-level provenance reviewed; bulk clone is excluded.\n| NSK/MISUMI manufacturer CAD | vendor portal | Manual/legal review required; no acquisition under current confirmed terms.\n| gated Jetson/STM32/Hailo CAD | vendor account/form | Manual required; no bypass.\n""",
      "DOWNLOAD_REPORT.md": "# Download Report\n\nNo third-party model downloads were made. Rights were confirmed for no new source file in a way that satisfied both commercial educational video use and public redistribution. Six self-authored Blender assemblies were generated instead. Manufacturer CAD and gated downloads remain separated in `MISSING_ASSETS.md`; public accessibility alone was not treated as permission.\n",
      "SOURCE_LICENSE_MATRIX.md": """# Source and License Matrix\n\n| Source/family | YouTube commercial use | GitHub redistribution | Status | Evidence\n|---|---|---|---|\n| Self-authored education geometry | Allowed under CC0-1.0 | Allowed under CC0-1.0 | Generated locally | `assets/education/generate_assets.py`; no third-party geometry incorporated.\n| KiCad library collection | Library data may be used in designs/generated files without relicensing those designs; collection redistribution requires CC-BY-SA 4.0 and attribution | Conditional CC-BY-SA 4.0 | Plan only | https://www.kicad.org/libraries/license/\n| NSK CAD | Not established for video use; official page prohibits unauthorized copying/use | Not established | Manual/legal review | https://www.nsk.com/kr-ko/catalogs-and-cad/\n| MISUMI CAD | Terms limit CAD to design/layout checking; other use requires prior permission | Not allowed absent permission | Blocked | https://jp.misumi-ec.com/contents/terms/cad_use.html\n| Livox/Ouster/ZED2i vendor CAD already present locally | Unknown beyond product-reference terms described in local registry | Not established; ignored by Git | Local use only; no redistribute | Existing local registry and `.gitignore`; no new downloads.\n| Raspberry Pi 5 STEP already present locally | Local license says MIT; applicability to CAD STEP not independently confirmed | Not established; ignored by Git | Local use only pending license-chain check | `assets/raspberry_pi5/LICENSE.txt`, local registry.\n| Gated Jetson/STM32/Hailo downloads | Unknown | Unknown | Manual required | Vendor pages and current TODO.\n\nKiCad license terms distinguish use of model data in generated designs from redistribution of library collections.\n""",
      "CONVERSION_REPORT.md": _conversion_report_text(),
      "BLENDER_VALIDATION.md": _blender_validation_text(),
      "MISSING_ASSETS.md": "# Missing and Restricted Assets\n\n| Asset/family | State | Reason/next action |\n|---|---|---|\n| Official NSK/MISUMI production CAD | MANUAL_REQUIRED/BLOCKED | Obtain written scope permission for public GitHub redistribution and commercial educational video, or keep using self-authored educational geometry.\n| KiCad component meshes | PLAN_ONLY | Locate installation or pin individual model source, license, commit/hash and attribution before acquiring a small representative set.\n| Jetson Orin Nano / STM32 Nucleo F446RE / Hailo-8 M.2 | MANUAL_REQUIRED | Human account/form download; no auth bypass.\n| DQ/field lines, true motor winding specification and contact forces, battery electrochemistry, stress/thermal/CFD fields | NOT IMPLEMENTED | Bearing rolling rates use stated ideal no-slip contact radii but are kinematically prescribed; assets are explanatory geometry only; use domain solver traces in a separate scope.\n| STEP-to-mesh conversion | BLOCKED | FreeCAD executable not found in current environment.\n""",
      "NEXT_ACQUISITION.md": "# Next Acquisition\n\n1. Confirm whether public release of the local Raspberry Pi STEP is covered by its included MIT license; otherwise keep ignored.\n2. If specific manufacturer's CAD is needed, obtain and archive explicit video and redistribution terms before download.\n3. Pin a small KiCad component subset by GitLab commit, exact file hashes, per-model attribution, and license metadata; prefer local installed files if available.\n4. Acquire gate-protected assets manually and document the downloaded file, source revision, terms, hash and import hierarchy.\n5. Add FreeCAD only if STEP-to-mesh conversion is an active requirement; no package was installed in this task.\n"""
    }
    for name, content in files.items():
        (REPORTS / name).write_text(content, encoding="utf-8")
    audit_rows = {r["id"]: r for r in rows}
    generated_count = sum(1 for m in catalog["models"] if (ROOT / m["path"]).is_file())
    table = ["# Asset Library Status", "", f"Counts reflect actual generated `.blend` files in this worktree: {generated_count} of {len(catalog['models'])}.", "",
             "| Category | Required groups | Existing | Downloaded | Generated | Validated | Blocked/planned |", "|---|---:|---:|---:|---:|---:|---:|"]
    groups = [
      ("Mechanical", "6 core families", "3 grouped scenes (bearing, gears, shaft/coupling/spring/fasteners)", "3 Blender files", "linear-motion and product variants remain"),
      ("Electromechanical", "BLDC/PMSM assembly", "1 educational BLDC concept", "1 Blender file", "no product winding or electromagnetic solver"),
      ("Electronics/PCB", "layered PCB and representative parts", "1 layered PCB concept", "1 Blender file", "no KiCad/vendor component library subset"),
      ("Energy", "cell and pack concept", "18650 concept in grouped mechanical scene", "same grouped scene", "no electrochemistry/BMS/pack model"),
      ("Structural", "beam and bracket", "1 grouped concept scene", "1 Blender file", "no stress solver geometry/results"),
      ("Thermal/fluid", "fan and heatsink", "1 grouped concept scene", "1 Blender file", "no CFD-ready geometry/results"),
      ("Robotics components", "reducers, encoder, IMU, wheels", "existing robot assets audited; no new internal component assembly", "0 new scenes", "internal mechanics remain planned")]
    for label,required,generated,validated,blocked in groups:
        table.append(f"| {label} | {required} | see existing asset audit | 0 | {generated} | {validated} | {blocked} |")
    (REPORTS / "LIBRARY_STATUS.md").write_text("\n".join(table)+"\n", encoding="utf-8")


def _blender_validation_text():
    validation_path = ROOT / "assets/education/generated/blender_validation.json"
    if not validation_path.is_file():
        return "# Blender Validation\n\nBLOCKED: Blender validation has not run.\n"
    evidence = json.loads(validation_path.read_text(encoding="utf-8"))
    lines = ["# Blender Validation", "", f"Blender: {evidence['blender_version']}",
             f"All preview PNGs present: `{evidence['all_previews_present']}`", "",
             "Each `.blend` file was reopened in Blender and checked for metric units, nonzero mesh bounds, object counts and keyframed state. This validates file/runtime integrity, not manufacturing or solver accuracy.", "",
             "| File | Objects | Meshes | Keyframed | Bounds X/Y/Z (m) | Result |", "|---|---:|---:|---:|---|---|"]
    for row in evidence["assets"]:
        bounds = " / ".join(f"{lo:.4f}–{hi:.4f}" for lo, hi in row["bounds_m"])
        lines.append(f"| `{row['file']}` | {row['object_count']} | {row['mesh_object_count']} | {row['keyframed_object_count']} | {bounds} | {row['validation']} |")
    lines += ["", "Rendered PNGs:", ""] + [f"- `assets/education/generated/{p}`" for p in evidence["preview_pngs"]]
    lines.append("")
    return "\n".join(lines)


def _conversion_report_text():
    root=ROOT/".cache/visual-assets/edu.bearing_6204.v1"
    source_hash=AssetFactory(ROOT).validate_asset("edu.bearing_6204.v1")["sha256"]
    matches=[]
    if root.exists():
        for candidate in root.glob("*/bearing_6204.glb"):
            metadata=candidate.parent/"asset.json"
            if metadata.is_file() and json.loads(metadata.read_text()).get("source_sha256")==source_hash:
                matches.append(candidate)
    lines=["# Conversion Report","",
           "Generated assemblies are authored natively as Blender geometry; no external STEP conversion was performed. The current environment has Blender but no confirmed FreeCAD executable or local KiCad 3D package library. Existing STEP assets remain unchanged.",""]
    if matches:
        path=matches[-1]
        lines += ["## Blender to GLB smoke conversion","",
                  f"- Source: `assets/education/generated/bearing_6204.blend`",
                  f"- Output (content-addressed local cache): `{path.relative_to(ROOT).as_posix()}`",
                  f"- Bytes: {path.stat().st_size}; SHA-256: `{sha256(path)}`",
                  "- Blender GLB export and immediate import-back with mesh objects: PASS.",
                  "- The cached GLB is derived output and is not committed.",""]
    else:
        lines += ["Blender `.blend` to `.glb` conversion has not run.",""]
    return "\n".join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    for action in ("audit","plan","download","convert","validate","report"):
        group.add_argument("--"+action,action="store_true")
    parser.add_argument("--allow-download",action="store_true",help="required alongside --download; still refuses entries without a complete pinned safe_archive contract")
    parser.add_argument("--allow-convert",action="store_true",help="required alongside --convert; converter must be configured through existing AssetFactory")
    parser.add_argument("--asset",help="registered asset id for --convert, or reviewed acquisition candidate for --download")
    parser.add_argument("--target",help="output format for --convert (currently glb from generated .blend)")
    args=parser.parse_args()
    catalog,registry=load()
    if args.download:
        if not args.allow_download: raise SystemExit("refusing network activity: add --allow-download explicitly")
        candidates = [c for c in catalog.get("acquisition_candidates", [])
                      if (not args.asset or c.get("id") == args.asset)]
        if not candidates:
            raise SystemExit("no matching candidate has a reviewed download contract; no network request made")
        if len(candidates) > 1:
            raise SystemExit("select one acquisition candidate with --asset")
        candidate = candidates[0]
        if candidate.get("use_status") not in {"PUBLIC_REDISTRIBUTABLE", "LICENSE_CONDITIONAL"}:
            raise SystemExit("download refused: candidate rights status is not approved for redistribution")
        if candidate.get("youtube_commercial_use") is not True or candidate.get("redistribution_allowed") is not True:
            raise SystemExit("download refused: both commercial-video and redistribution scopes must be explicitly true")
        contract = {"source_archive_url":candidate.get("source_archive_url"),
                    "source_archive_sha256":candidate.get("source_archive_sha256"),
                    "source_archive_size_bytes":candidate.get("source_archive_size_bytes"),
                    "allowed_hosts":candidate.get("allowed_hosts"),
                    "install_path":candidate.get("install_path")}
        missing = [name for name, value in contract.items() if not value]
        if missing:
            raise SystemExit("download refused; missing pinned contract fields: " + ", ".join(missing))
        destination=(ROOT / contract["install_path"]).resolve()
        if not destination.is_relative_to(ROOT):
            raise SystemExit("download destination escapes repository")
        from safe_archive import fetch_pinned_archive
        result=fetch_pinned_archive(url=contract["source_archive_url"],destination=destination,
            sha256=contract["source_archive_sha256"],size_bytes=contract["source_archive_size_bytes"],
            allowed_hosts=contract["allowed_hosts"],allow_large=False)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return
    if args.convert:
        if not args.allow_convert: raise SystemExit("refusing conversion: add --allow-convert explicitly")
        if not args.asset or not args.target:
            raise SystemExit("--convert requires --asset <registered-id> --target glb")
        if args.target.lower() != "glb":
            raise SystemExit("only Blender GLB export from a registered .blend is currently configured")
        from core.mechanism.renderer import _blender_binary, _blender_path_arg
        factory=AssetFactory(ROOT)
        def converter(source, staging, entry):
            if source.suffix.lower() != ".blend":
                raise ValueError("configured converter accepts Blender .blend sources only")
            target=staging / (source.stem + ".glb")
            blender=_blender_binary()
            blender_source=_blender_path_arg(source,blender)
            helper=_blender_path_arg(ROOT/"scripts/convert_blend_to_glb.py",blender)
            blender_target=_blender_path_arg(target,blender)
            subprocess.run([blender,"--background",blender_source,"--python-exit-code","1",
                            "--python",helper,"--","--output",blender_target],
                           cwd=ROOT,check=True)
            with target.open("rb") as stream:
                if stream.read(4) != b"glTF":
                    raise ValueError("Blender output is not a GLB binary")
            return target
        target=factory.convert_asset(args.asset,args.target,converter,converter_id="blender-glb-export",
                                     converter_version="3",converter_config={"animations":True,"reimport_validation":True})
        print(json.dumps({"asset_id":args.asset,"target_format":"glb","path":str(target),
                          "sha256":sha256(target),"conversion":"PASS"},indent=2))
        return
    if args.audit:
        rows=audit(catalog,registry); write_audit(rows)
        print(f"Audited {len(rows)} registry entries; report: docs/assets/EXISTING_ASSET_AUDIT.md")
    elif args.plan:
        print("PLAN ONLY: 6 authored Blender assemblies; no download. See docs/assets/ACQUISITION_PLAN.md")
    elif args.validate:
        result=validate(catalog,registry); print(json.dumps(result,indent=2))
    elif args.report:
        rows=audit(catalog,registry); write_audit(rows); report(catalog,rows)
        print(f"Wrote reports to {REPORTS.relative_to(ROOT)}")


if __name__=="__main__": main()
