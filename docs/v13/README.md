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

The Vendor CAD failure from run #28 was fixed in commit `9a43b205`: local Livox/Ouster/ZED 2i CAD is optional, while the catalog and license boundaries and Git tracking prohibition remain unconditional checks.

[AI trace run #29](https://github.com/hinoonyaso/make_simulation/actions/runs/38062554626) succeeded and its log records all 155 repository unit tests passing. This is the full CPU regression job; it is distinct from the V13-only education workflow.

The V13 workflow runs the two education test modules, validates the asset registry and catalog, validates a concept-only plan, compiles V13 Python modules, and renders a short Manim-only smoke. It uses the locked `sim-render` dependency group, so it does not install V12 solver or robotics test dependencies. It checks exact 960×540, 30 fps H.264 output, VTT and production report presence, then runs a full decode. The preview, reports, validation output and logs are uploaded as one artifact. Scoped `pull_request` and `push` filters cover education files and common V13 dependencies; `workflow_dispatch` remains available. The updated workflow has passed local checks in the locked render-only environment. Its GitHub Actions result is pending until this workflow change is pushed and the run completes.

| Gate | Result | Evidence / boundary |
|---|---|---|
| Full unittest suite | PASS, 155/155 | GitHub Actions AI trace run #29 |
| V13 education tests | PASS, 16/16 | `uv sync --locked --only-group sim-render --no-install-project` environment |
| Asset registry and catalog validation | PASS | 39 registry entries; six generated model hashes |
| Education plan | PASS | Concept-only smoke spec |
| Manim smoke preview | PASS | 960×540, 30 fps, silent; VTT and production report; full decode |
| Blender render | PASS (recorded R6 local run) | Windows Blender 5.2.1 launched from WSL; not executed by Ubuntu CI |
| Narration/TTS | NOT TESTED | Smoke does not call Edge TTS or Whisper |
| Narrated 1080p final validation | NOT TESTED | Smoke is a low-resolution silent preview |

## Runtime notes

- The recorded bearing R6 render used Blender 5.2.1 and Manim 0.21.0 from the local WSL setup. Its evidence is in `EDUCATIONAL_QA.md`; it does not mean the same Blender integration is available in every WSL or CI environment.
- The 2026-10-11 Manim smoke used Manim 0.21.0 from the locked render-only group. It completed with a missing-SoX startup warning; this silent path does not use SoX. Do not infer that TTS/audio tooling was checked.
- The Blender shot and Manim comparison shot are procedural educational graphics, not CAD-accurate geometry or contact/friction solver outputs.
