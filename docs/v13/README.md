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

Latest rendered preview: `pilots/v13_education/output/lessons/bearing-v13-preview-r5/preview.mp4` (84 seconds, 960×540, 30 fps, silent). The output directory is ignored/generated. V9 manifest media validation and full MP4 decode passed. Sampled frames were reviewed, but full normal-speed playback and narration review remain incomplete. See `EDUCATIONAL_QA.md` for the observed limits. A fresh Edge TTS authorization is required before sending this new Korean script to the external TTS service.

## Runtime notes

- Blender 5.2.1 was found and rendered successfully from WSL by launching the installed Windows executable. Blender emitted harmless absolute-path portability warnings for bundled resources and the Windows Malgun font.
- Manim 0.21.0 rendered successfully; its startup warns that SoX is missing. This lesson's Manim scene does not use SoX, so the warning did not block rendering.
- The Blender shot and Manim comparison shot are procedural educational graphics, not CAD-accurate geometry or contact/friction solver outputs.
