# Source and License Matrix

| Source/family | YouTube commercial use | GitHub redistribution | Status | Evidence
|---|---|---|---|
| Self-authored education geometry | Allowed under CC0-1.0 | Allowed under CC0-1.0 | Generated locally | `assets/education/generate_assets.py`; no third-party geometry incorporated.
| KiCad library collection | Library data may be used in designs/generated files without relicensing those designs; collection redistribution requires CC-BY-SA 4.0 and attribution | Conditional CC-BY-SA 4.0 | Plan only | https://www.kicad.org/libraries/license/
| NSK CAD | Not established for video use; official page prohibits unauthorized copying/use | Not established | Manual/legal review | https://www.nsk.com/kr-ko/catalogs-and-cad/
| MISUMI CAD | Terms limit CAD to design/layout checking; other use requires prior permission | Not allowed absent permission | Blocked | https://jp.misumi-ec.com/contents/terms/cad_use.html
| Livox/Ouster/ZED2i vendor CAD already present locally | Unknown beyond product-reference terms described in local registry | Not established; ignored by Git | Local use only; no redistribute | Existing local registry and `.gitignore`; no new downloads.
| Raspberry Pi 5 STEP already present locally | Local license says MIT; applicability to CAD STEP not independently confirmed | Not established; ignored by Git | Local use only pending license-chain check | `assets/raspberry_pi5/LICENSE.txt`, local registry.
| Gated Jetson/STM32/Hailo downloads | Unknown | Unknown | Manual required | Vendor pages and current TODO.

KiCad license terms distinguish use of model data in generated designs from redistribution of library collections.
