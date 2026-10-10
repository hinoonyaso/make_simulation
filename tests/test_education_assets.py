from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("acquire_education_assets", ROOT / "scripts/acquire_education_assets.py")
acquire = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acquire)


class EducationAssetLibraryTests(unittest.TestCase):
    def test_registry_and_catalog_metadata(self):
        catalog, registry = acquire.load()
        result = acquire.validate(catalog, registry)
        self.assertEqual(result["registry_entries"], len(registry["assets"]))
        self.assertGreaterEqual(result["catalog_models"], 6)
        self.assertEqual(len({x["id"] for x in registry["assets"]}), len(registry["assets"]))

    def test_vendor_assets_present_but_not_clone_tracked(self):
        rows = acquire.audit(*acquire.load())
        indexed = {x["id"]: x for x in rows}
        for asset_id in ("blender.livox_mid360.v1", "blender.ouster_os0.v1",
                         "blender.ouster_os1.v1", "blender.ouster_osdome.v1", "blender.zed2i.v1"):
            self.assertTrue(indexed[asset_id]["exists"], asset_id)
            self.assertGreater(indexed[asset_id]["file_count"], 0, asset_id)
            self.assertFalse(any(f["git_tracked"] for f in indexed[asset_id]["files"]), asset_id)

    def test_acquisition_modes_default_safe(self):
        catalog, _ = acquire.load()
        self.assertEqual(catalog["default_acquisition_mode"], "plan")
        restricted = {x["id"]: x for x in catalog["restricted_existing"]}
        self.assertEqual(restricted["blender.zed2i.v1"]["status"], "LOCAL_USE_ONLY")

    def test_all_generated_models_and_previews_exist(self):
        catalog, _ = acquire.load()
        for model in catalog["models"]:
            path = ROOT / model["path"]
            self.assertTrue(path.is_file(), model["id"])
            self.assertGreater(path.stat().st_size, 1024, model["id"])
            self.assertTrue((path.parent / (path.stem + ".png")).is_file(), model["id"])

    def test_bearing_rolling_rates_follow_declared_contact_geometry(self):
        meta=json.loads((ROOT/"assets/education/generated/bearing_6204.json").read_text())
        motion=meta["motion"]
        self.assertAlmostEqual(motion["cage_angular_speed_over_inner"],
                               motion["inner_contact_radius_m"] /
                               (motion["inner_contact_radius_m"]+motion["outer_contact_radius_m"]))
        self.assertAlmostEqual(motion["ball_spin_angular_speed_over_inner"],
                               -motion["inner_contact_radius_m"]/(2*motion["ball_radius_m"]))
        self.assertIn("no contact solver",motion["assumption"])

    def test_spur_gear_center_distance_matches_pitch_radii(self):
        meta=json.loads((ROOT/"assets/education/generated/spur_gears_20_40.json").read_text())
        expected=meta["module_m"]*(meta["pinion_teeth"]+meta["gear_teeth"])/2
        self.assertAlmostEqual(meta["center_distance_m"],expected)
        self.assertAlmostEqual(meta["ratio"],meta["gear_teeth"]/meta["pinion_teeth"])

    def test_download_requires_reviewed_candidates(self):
        import subprocess
        result = subprocess.run([sys.executable, str(ROOT / "scripts/acquire_education_assets.py"),
                                 "--download", "--allow-download"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no matching candidate has a reviewed download contract", result.stderr)

    def test_safe_archive_rejects_traversal_and_symlink(self):
        from safe_archive import safe_extract_archive
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            traversal = root / "traversal.zip"
            with zipfile.ZipFile(traversal, "w") as zf:
                zf.writestr("../escape.txt", "bad")
            with self.assertRaises(ValueError):
                safe_extract_archive(traversal, root / "out1")
            link = root / "link.zip"
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            with zipfile.ZipFile(link, "w") as zf:
                zf.writestr(info, "../../escape")
            with self.assertRaises(ValueError):
                safe_extract_archive(link, root / "out2")

    def test_blender_generator_is_explicit_and_contains_required_families(self):
        source = (ROOT / "assets/education/generate_assets.py").read_text()
        for token in ("bearing_stage", "gear_stage", "motor_stage", "pcb_stage",
                      "mechanism_stage", "structure_fluid_stage", "animation_ready"):
            self.assertIn(token, source)
        self.assertIn("not involute", source)
        self.assertIn("no contact solver", source)


if __name__ == "__main__":
    unittest.main()
