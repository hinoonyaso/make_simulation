# V13 Education-First Foundation

V13 adds a solver-optional Lesson Spec and planner that emits the established V9 `visual_manifest.json` and uses the V12 integer-frame timeline. Existing `produce_video.py` execution routes remain unchanged.

Validate and inspect a concept-only plan:

```bash
uv run python scripts/produce_lesson.py --spec examples/education/bearing.json --plan-only
```

Render a short Manim-only CI smoke:

```bash
uv run python scripts/produce_lesson.py --spec examples/education/education_smoke.json --preview --manim-only
```

Render the full bearing preview with Blender and Manim:

```bash
uv run python scripts/produce_lesson.py --spec examples/education/bearing.json --preview
```

The default preview is silent, writes sentence-level VTT captions and burns the same captions into the MP4. `--with-tts` explicitly invokes the existing Edge TTS and Whisper alignment workflow; it is not run automatically. No solver is needed for the bearing lesson, and no measured friction/contact result is claimed. Full narrated output is only reported after TTS, caption timing, audio mux and media validation succeed.

## Pilot output and review status

Latest recorded bearing preview: `pilots/v13_education/output/lessons/bearing-v13-preview-r6/preview.mp4` (84 seconds, 960×540, 30 fps, silent). This output directory is ignored/generated and is not present in a clean clone. V9 manifest media validation and full MP4 decode passed for that recorded preview. Sampled frames were reviewed, but full normal-speed playback and narration review remain incomplete. See `EDUCATIONAL_QA.md` for the evidence and limits. A fresh Edge TTS authorization is required before sending this Korean script to the external TTS service.

On 2026-10-11, the Manim-only smoke command above was rerun from the pushed-branch source using Manim 0.21.0. It produced a 960×540, 30 fps silent MP4 under a temporary directory and passed full decode. Manim printed a missing-SoX warning; SoX is not used by this silent path. This smoke render is not the bearing preview or a narrated final.

## CI status

The latest observed integration workflow run is [run #28](https://github.com/hinoonyaso/make_simulation/actions/runs/38061841065). It failed because `test_vendor_assets_present_but_not_clone_tracked` required proprietary, ignored Livox/Ouster/ZED 2i CAD files in a clean clone. The test now always checks registry/catalog paths, local-use-only and redistribution metadata, and Git tracking prohibition; it checks local file contents only when a developer has those optional files. The updated test passes without the vendor CAD. The full local suite and the individual V12/V13 suites pass (155, 19 and 16 tests respectively). No Actions run after this fix has been confirmed yet; the integration workflow is manually dispatched, so local checks are not a remote CI result.

## Runtime notes

- The recorded bearing R6 render used Blender 5.2.1 and Manim 0.21.0 from the local WSL setup. Its evidence is in `EDUCATIONAL_QA.md`; it does not mean the same Blender integration is available in every WSL or CI environment.
- The 2026-10-11 Manim smoke used Manim 0.21.0 and completed despite the missing-SoX warning because this silent render path does not use SoX. Do not infer that TTS/audio tooling was checked.
- The Blender shot and Manim comparison shot are procedural educational graphics, not CAD-accurate geometry or contact/friction solver outputs.
