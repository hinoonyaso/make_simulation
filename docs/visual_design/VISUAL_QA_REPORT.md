# Unified Visual Design System — Visual QA Report

## Result summary

The V14.5 stabilization pass found and corrected two visible problems: the Battery asset's inherited `-3 EV` exposure defeated both selected profiles, and the Manim layout helper treated an upper-left anchor as an object-center coordinate. Battery contrast/title placement, Manim bounding-box placement, and representative TEB frames were checked from actual renders. No P0/P1 visual blocker was seen in the inspected stills. Overall QA remains `INCOMPLETE`: a full mixed Battery movie and full-length normal-speed human review were not performed.

## Before / after evidence

| Sample | Before evidence | Updated evidence | Finding |
|---|---|---|---|
| Battery 18650 profile | Blender 5.2.1 stills before fix: `/tmp/v145-battery-output/battery-dark/battery_still.png` (`da103e…0182`) and `battery-light/battery_still.png` (`ee546d…2b519`). Both inherited the asset's `-3 EV`; the Light canvas corner was RGB `(38,40,42)`. The header was at the top frame edge. | `pilots/v14_education/output/lessons/v145-stabilization-qa/battery_{technical_dark,studio_light}_frame_{0001,0450}.png` | Scene now sets exposure/gamma to `0/1`; Light canvas corner is `(149,152,155)`. Header moved down into the frame. Cell, electrode and gauge colors retain their semantic mapping. Both profiles show frame 1 and mid-SOC frame 450. |
| Battery Manim layer | No new V14.5 render was available. | `.../battery_manim_{technical_dark,studio_light}_layer.mp4` in the same ignored QA directory | Both registered Manim layers rendered from the validated Solver context: 24.033 s, 854×480, 30 fps, 721 frames; FFmpeg full decode passed. These are renderer layers, not a mixed Blender+Manim lesson preview. |
| TEB Blender | Local reference MP4 `/home/sang/make_simulation/pilots/01_teb_reference/output/pilot_teb_reference.mp4`, SHA-256 `2ae70645da50bd48c0155de69f02d0222816c86a5174a46c60b55216f555b615`, 71.2 s, 1920×1080, 30 fps. Source/render provenance for this ignored local artifact is not recorded, so it is not treated as a controlled pixel comparison. | `pilots/01_teb_reference/output/blender/S1_final/still_0180.png` and `S3_final/still_0180.png` | Re-rendered corresponding S1/S3 states from the checked-out TEB source at 1920×1080, 30 fps, 64 samples, Blender 5.2.1 LTS, Studio Light. Compared against frames extracted at 6.0 s and 65.2 s from the reference video. Framing, drum/robot separation, studio floor and band/trail colors were visually consistent; no regression seen in these samples. |
| TEB Manim | Same local reference MP4; Manim segment source provenance is not embedded in the old video. | `pilots/v14_education/output/lessons/v145-stabilization-qa/teb_manim_1080p30.mp4` | Current `BandDissection` source rendered at 1920×1080, 30 fps, 47.6 s / 1428 frames; H.264 full decode passed. The source chapter uses the existing dark palette and band trace. A 30 s representative frame was inspected. |
| Manim layout | `center=False` passed `[left, top]` to `move_to()`, placing the object's center there and allowing its real bounds to spill outside the region. | `tests/test_visual_design_layout.py`; `/tmp/v145-layout-final/videos/v145_layout_smoke/1080p2/LayoutSmoke.mp4` | Real Manim Text, MathTex and VGroup bounds are tested for upper-left anchoring, fit/scaling, center behavior, multiple frame aspects, invalid margins and region bounds. A 1080p Manim scene smoke rendered and fully decoded. |
| Bearing / gear | Existing R5/V14.1 local examples documented below; neither source was changed in this stabilization pass. | Existing V14.5 Bearing/Gear renders in `pilots/v13_education/output/lessons/v145-bearing-design/` and `pilots/v14_education/output/lessons/v145-gear-design/` | Existing samples remain evidence for those profiles. This pass did not rerender them. |

## Reproducibility record

The render outputs below remain local and are ignored by Git. Source revisions and input/output hashes identify what can be reproduced. The previous local TEB MP4 is also ignored and has no embedded source commit or render settings; those fields are explicitly unknown rather than inferred.

### Battery

| Item | Value |
|---|---|
| Source revision | `6373b928b05884e66f25d74764999dea6dad10ac` (`battery_scene.py` profile exposure/title fix) |
| Solver | PyBaMM 26.10.0.0, IDAKLUSolver, CPU, SPM/Chen2020, 1C, 1800 s, 361 samples at 5 s |
| Solver run / result | `v145-battery-qa`; result SHA-256 `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25` |
| Config SHA-256 | `35afef525c0a4546fbfb4caae3fa0141fb9f5b450dffc8d0c98b15b1545dc3ff` |
| Asset | `edu.mechanical_primitives.v1`, SHA-256 `d37958e2b25b6deb484dc45ecd5d69cf51c26dde2f6283099d749ef2743a0cc1` |
| Blender | Blender 5.2.1 LTS, EEVEE, 960×540, 30 fps; profiles `technical_dark` and `studio_light`; still frames 1 (0 s) and 450 (~14.97 s presentation / ~895 s Solver time) |
| Output | Technical Dark frame 1 `da8a33e24a69b61f61c76fabb463c3a88c8edce083bd4a307a215a2d9baedc5d`; frame 450 `5648c4668eb5746aa84f73d5b7f6c436c140e6d0a98c98ac309866baae917c8b`. Studio Light frame 1 `4b9f4291feb06c0c9290ee575d5e1fd0a218a06b320159f8abec47b921d6bb57`; frame 450 `2264ac803c0da22be08dc41b25270f319abfe4285ee2ddb7c898c4e876d3554e`. |
| Manim layer | Manim CE 0.21.0; each profile 854×480, 30 fps, 24.033 s, 721 frames; hashes: Dark `05d8808bd308556d6681edfd25f39e6982de673f976f6fc2ac33479301ce5b20`, Light `9b0e27ad3cf0dd66ee74b070203ecb10cb814c50e5743c3a22ca02922ab4c7c3`. |

### TEB

| Item | Value |
|---|---|
| Source revisions | `pilots/01_teb_reference/{blender_shots.py,manim_shot.py}` last changed at `2af957f442d8919946cabd32e30152113bc47a20`; shared `studio_utils.py` profile implementation at `56157455d783c9617a5dba2feeb58f1523090595`. Files were unchanged in this pass. |
| Inputs | `band_trace.json` SHA-256 `5ca8f34090e147dad85d63a68014e51b2f6c46e2479ef1e0413671c97e5b800a`; `drive_trace.json` SHA-256 `ffa045f3400107f5c8cc2ccb6342dc6b5aa6672285c0709c43064358c935d9fb`; manifest SHA-256 `939a14c065e660d29b0128230dd6e28de45d68c62189cb81a731203ad7690fb8`. |
| Blender render | `render.sh S1 FINAL stills 180` and `render.sh S3 FINAL stills 180`; Blender 5.2.1 LTS, Studio Light default, 1920×1080, 30 fps, 64 samples. The stills correspond to `(180−1)/30 = 5.967 s` within each shot. S1 SHA-256 `9103643061a4bc2c0766a7a766d55c2e2bd042b7f2e5bb6790f7223ba9e5904d`; S3 `df2625d4b5d60ec2c5c66dc7ddc5f92e5c56bc4b92250c18d5e673d60eac782a`. |
| Manim render | `manim -qh --fps 30 ... BandDissection`; Manim CE 0.21.0, 1920×1080, 30 fps, 47.6 s / 1428 frames. Output SHA-256 `2d61c06c3b635e9082ba9166f0fa6e81e8ad58a12d92f0a7c290d06a9a840295`. |
| Before artifact limits | The old MP4 reports 1920×1080/30 and 71.2 s, SHA-256 above. Its exact producing source commit, renderer build/settings, trace hashes and per-frame render parameters cannot be recovered from the untracked file. Comparison is visual at matched nominal shot times, not a controlled numeric image-difference claim. |

## Automated checks

| Check | Result |
|---|---|
| Full unittest suite | PASS — 236 tests, including real Manim object layout bounds. |
| Compileall | PASS — `core scripts tests assets/education pilots/v13_education pilots/v14_education`. |
| Visual design / scene style | PASS — all six V13/V14 Blender and Manim scenes. |
| Token contrast | PASS — Studio Light 12.019:1 primary / 6.683:1 secondary; Technical Dark 17.620:1 / 6.191:1. |
| Korean font coverage | PASS — Blender NanumGothic TTF and Manim NanumGothic Hangul coverage. |
| Asset registries | PASS — 39 registry entries; 6 catalog models and 6 generated assets. |
| Battery Solver result | PASS — saved result schema/hash validation, 361 samples, 1800 s. |
| Battery Blender stills | PASS — both profiles, frames 1 and 450; asset-load report PASS; images inspected. |
| Battery Manim layer | PASS — both profiles, H.264 and full decode; this does not validate a final mixed lesson. |
| TEB Blender | PASS — representative current-source S1/S3 1080p stills rendered and compared against local reference frames. |
| TEB Manim | PASS — current source rendered at 1080p30 and full decoded. |
| Manim layout scene | PASS — real Text/MathTex/VGroup scene rendered at 1080p and full decoded. |
| GitHub Education Renderer | FAIL — run [53](https://github.com/hinoonyaso/make_simulation/actions/runs/38495615435), head `404d14ac6faf168f09b69e8e72224ea7d0f3c9ec`; complete unittest regression could not import `test_visual_design_layout` because Manim was absent in that job environment. |
| GitHub AI Trace | FAIL — run [123](https://github.com/hinoonyaso/make_simulation/actions/runs/38495615415), same head; complete unittest regression could not import `test_visual_design_layout` because Manim was absent in that job environment. |

`analyze_visual_render.py` is candidate sampling only. It does not establish readability, motion quality, full decode, learner comprehension or a design score. The user-visible video outputs listed above are local/ignored; generated product media is not included in the PR.

## Render defects found and fixed

1. Battery `.blend` asset stored `-3.0 EV`. Setting only AgX transform/look left both palettes too dark. The Battery scene now explicitly sets exposure to `0.0` and gamma to `1.0` after opening the asset; actual renders showed the Light background change from RGB `(38,40,42)` to `(149,152,155)`.
2. Battery heading was too close to the top edge. Its anchor moved from `y=.052` to `.046` in camera-local space; both profile renders show an inset header.
3. `place_in_layout(center=False)` aligned object centers rather than bounding-box corners. It now shifts the fitted bounding box to the region's safe upper-left and rejects unusable/non-finite margins. Real Manim tests cover text, equation, group, oversized and center cases.

## Review status and remaining risks

- Representative still review: PASS for four Battery images, the current TEB S1/S3 comparison frames, and Manim layout/profile samples. No inspected still showed a blocker/high-severity defect.
- Motion QA: `INCOMPLETE`. TEB Manim rendered in full, but the old narrated TEB movie was not watched end-to-end at normal speed; the Battery run is renderer-layer output plus stills, not a mixed movie. No motion claim is made for Battery.
- Audio QA: `NOT APPLICABLE` to the new silent render layers; audio in the old TEB reference was not re-reviewed.
- Before/after provenance: old TEB render source/settings are unknown, as stated above. The comparison is not presented as a controlled render benchmark.
- Blender logs a deprecation warning for `Material.use_nodes` in the Battery emission helper on Blender 5.2.1. Rendering succeeds; migration is not part of this fix.
- The first remote runs failed because the full CPU regression workflows intentionally install no Manim, but the new Manim-specific test imported Manim unconditionally. The test now raises a clear unittest skip when `sim-render` is absent; with locked local dependencies the full 236-test suite passes. A post-fix GitHub run is still required.
- PR #10 remains Draft and stacked on PR #9's branch. GitHub runs are in progress; no PR was made Ready and no merge was attempted.

No overall `10/10` score is claimed. The updated profile and layout checks are supported by real renders and bounds tests, while mixed Battery playback and full-speed human review remain open.
