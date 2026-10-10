# Robotics / AI Visual Video V9 — Source-Informed Lite

High-quality, low-token Codex pipeline for robotics/AI educational videos.

Default route: `Director -> optional shared trace -> Manim/Blender -> one real-render review -> Resolve -> optional YouTube`.

V9 keeps V8 Lite's small agent graph, but strengthens **production primitives** using general patterns found in public source repositories from 3Blue1Brown, Welch Labs, Reducible, Primer, and Sebastian Lague. No creator scene code is copied. `SOURCE_PATTERNS.md` is provenance only and should not be preloaded.

Key upgrades:
- state-transition storytelling instead of slide replacement;
- shared computed traces for data/model/simulation visuals;
- selective-density helpers for networks/attention/graphs;
- reusable stateful Blender objects + `.blend` assets;
- automatic camera framing from object bounds;
- deterministic manifest/trace/delivery gates;
- 1080p minimum, 1440p preferred for line/text-heavy masters.

Start with `ROUTING.md`.

## V11.2 run isolation and trace replay

The V11 mechanism CLI now writes each run under `output/runs/<topic>-<run-id>/` with the request, adapter config, validated trace, visual plan, V9-compatible manifest, media and production report. The ID partitions by topic, normalized input/config, validated trace, renderer mode, adapter/code fingerprint and the trace's asset provenance. A completed matching run is reused by default only after its media passes full decode again. Incomplete or conflicting directories are kept intact and rejected; `--force` creates a timestamped sibling. `--run-id` is an explicit directory name and will never overwrite an existing run.

```bash
# Execute a numerical adapter and render a 540p30 technical preview.
uv run python scripts/produce_video.py --topic quantization --preview

# Replay the exact saved trace without generating a new mechanism result.
uv run python scripts/produce_video.py --topic quantization --mode replay \
  --trace output/runs/quantization-<run-id>/trace.json --preview

# Use the completed run cache; use --no-reuse to refuse a cache hit.
uv run python scripts/produce_video.py --topic quantization --preview
```

The replay validator checks schema, topic (including legacy V9 asset/family identity), and the domain equations before planning or rendering. Beat count follows the validated topic stages and trace content; duration is estimated from trace complexity unless an already measured narration duration is supplied with `--narration-duration`. This value only allocates visual beat time; it does not create speech or captions. V11.2 currently emits silent technical previews/renders. It does not claim full production.

## V10 RAG production

The current runnable V10 AI path supports RAG only. Replay a checked-in AI trace, or execute a new local lexical TF-IDF run from a document and question. It does not claim semantic embeddings or LLM generation. `--render auto` includes the trace-matched Three.js projection when local browser tooling is available and records a Manim fallback otherwise.

```bash
uv run python scripts/produce_ai_video.py \
  --topic rag \
  --trace pilots/v10_rag_poc/data/ai_trace.json \
  --render auto --silent
```

For a fresh local lexical run, replace `--trace ...` with `--document path/to/document.txt --question "your question"`. Preview and final artifacts are written to `pilots/v10_rag_poc/output/runs/`. See the [V10 RAG README](pilots/v10_rag_poc/README.md) for execution limits, validation and optional audio instructions. Remote GitHub Actions and normal-speed audio review must be reported from actual runs; local PASS does not imply either.

## V11 universal mechanism previews

The additive V11 capability registry currently runs RAG, NumPy quantization (weight-only or separate weights and activations), synthetic-candidate IoU/NMS, a numerical MCU PID motor model, a NumPy single-head Self-Attention calculation, and the existing fixed-base MuJoCo H1 arm experiment. Korean aliases and ambiguity are resolved by the registry. Inspect actual levels and limitations before routing a topic:

```bash
uv run python scripts/inspect_capabilities.py
uv run python scripts/produce_video.py --topic quantization --preview
uv run python scripts/produce_video.py --topic nms --preview
uv run python scripts/produce_video.py --topic mcu_pid --preview
uv run python scripts/produce_video.py --topic 자기주의 --preview
uv run python scripts/produce_video.py --topic robot_kinematics --robot unitree_h1 --preview
uv run python scripts/manage_assets.py search --category environment
```

These are silent technical previews, not narrated/reviewed finished videos. Self-Attention uses toy numerical vectors, not a trained Transformer. The secure pinned-archive helper exists, but no environment currently has enough verified metadata to download, and no environment has passed a simulator load/render test on this host. Clearpath/Gazebo, ManiSkill/SAPIEN and robosuite status is documented in [environment validation](docs/v11/environments/ENVIRONMENT_VALIDATION.md). Other catalog topics remain planned or trace-only unless the registry says otherwise. See [V11 implementation and limits](docs/v11/IMPLEMENTATION_REPORT.md).

## V11.3 integrated render backends

The common CLI now routes `robot_kinematics --render blender` through the existing H1 mesh trace exporter/renderer, and `object_detection` through the verified YOLO11n CPU inference adapter. Blender plays the validated MuJoCo trace; it does not rerun physics. YOLO uses the pinned checkpoint hash and records the original image hash; replay checks the same image and does not rerun inference. Install Ultralytics 8.3.0 in the active environment only when real YOLO inference is requested.

## V11.4 routing and timeline

`--visual-goal` steers renderer selection by the evidence the explanation needs: H1 `motion_3d` requires the Blender trace renderer, H1 comparison stays in Manim, YOLO uses image-space Manim, and RAG can use the recorded-vector Three.js embedding segment. `--render auto` runs a lightweight process preflight; `scripts/inspect_capabilities.py --topic <topic> --preflight` shows the decision before rendering. Explicit Blender failures remain blocked.

Each run stores a `mechanism-timeline/v1` contract with contiguous integer frame ranges. Manim, YOLO, H1 trace export and the existing four-beat RAG scene use that timeline. H1 source time is mapped separately from presentation time. RAG's Three.js section uses the exact embedding-phase frame range. Run identity includes renderer choice, visual goal, timeline, relevant code/runtime versions and local asset hash. See [V11.4 routing](docs/v11/V11_4_RENDERER_ROUTING.md), [timeline contract](docs/v11/V11_4_TIMELINE_CONTRACT.md), and [integration report](docs/v11/V11_4_INTEGRATION_REPORT.md).

```bash
uv run python scripts/produce_video.py --topic robot_kinematics --robot unitree_h1 \
  --mode replay --trace pilots/v10_mujoco_arm/data/trace.json --render blender --preview
uv run --with ultralytics==8.3.0 python scripts/produce_video.py --topic object_detection \
  --input /path/to/image.jpg --model /path/to/verified-yolo11n.pt --preview
uv run python scripts/produce_video.py --topic object_detection --mode replay \
  --trace output/runs/object_detection-<run-id>/trace.json --preview
```

RAG Preview and Final select their respective report entries and validate the reported media, dimensions, 30 fps and full decode. Cache reuse also checks the expected output path, render specification, media metadata and SHA-256. Storyboard beats carry explicit phase IDs which the common Manim scene checks against its transition map. See the dated [V11.3 integration report](docs/v11/V11_3_INTEGRATION_REPORT.md) for actual local evidence and unrun remote CI status.

## Explanation craft

Director now plans the visible cause, decisive comparison/constraint, and consequence of the central question. Manim/Blender expose that evidence with purposeful framing and phrase timing; Reviewer reports educational inspection separately from technical PASS. Narration guidance includes deliberate pauses and Korean terminology pronunciation. The next real preview must demonstrate these changes; existing published videos are unchanged. Reference sources, access limits, decisions, and tradeoffs are in [SOURCE_PATTERNS.md](SOURCE_PATTERNS.md#2026-10-explanation-craft-update-user-selected-references).

## Discovery and critical-preview update

Full explainers now validate their hardest inference as a short moving excerpt with measured narration before full rendering. Director plans expectation, visible test, mechanism and supported transfer in existing manifest fields. Reviewer records interpretation before consulting source data, and separates comprehension, motion and voice inspection. Unavailable playback/listening remains incomplete, even with technical PASS. This preserves the single-manifest interface and uses local implementations when shared kits are protected.

The change addresses observed pilot limitations: detached 3D/2D presentation, insufficiently tested inference, and frame/timing checks being mistaken for full audio/motion acceptance. It does not establish creator parity. Tradeoff: an extra small preview/listening pass before the expensive render; it can reuse previously approved equivalent media. Shared kits, original episodes and existing video outputs are not changed by this skill update. Behavioral effectiveness still requires the next real production and viewer feedback.

Validation for this update: five skill folders pass `skill-creator/scripts/quick_validate.py`; Director/Reviewer TOML and review-template YAML parse; `scripts/validate_codex_setup.py` passes all 10 agent configurations; `git diff --check` passes. Skill validation used system Python because the project environment lacks PyYAML; no dependency was added. These checks establish format and wiring, not the educational quality of a future video.

## Physics-backed robotics production

The user's selected next direction preserves the current discovery explanation and adds physics-backed Blender setup/consequence. A capable installed engine computes actuation/contact first; Manim and Blender then explain/render the same recorded run. Blender may be the renderer for another simulator. Reference plans and actual body trajectories remain separate; pose replay, kinematic integration and contact-resolving physics are explicitly distinguished.

The detailed run contract is in [Blender evidence rules](core/blender-robotics-simulation-skill/references/evidence.md). Existing manifest evidence enums and V9 schema are unchanged. Physics acceptance now has a separate review field: solver provenance and relevant physical checks cannot be replaced by realistic rendering or schema PASS. Shared kits and finished episodes are untouched. This update supplies production/review instructions; it does not execute or validate a new physical simulation. Engine choice, model fidelity and solver stability still require the next episode's environment inspection and experiment.

Physics skill update validation: four affected skill folders pass `quick_validate.py`; updated agent TOML and review YAML parse; `validate_codex_setup.py` passes all 10 agent configs; `git diff --check` passes. Cross-skill evidence links were corrected to their actual bundle paths after the wiring check identified unresolved references. These checks validate instructions/configuration only, not a physics engine or runtime experiment.

## MuJoCo local environment

The project pins the official MuJoCo Python bindings to `3.7.0` in `pyproject.toml` and `uv.lock`. Install or synchronize with `uv sync`, then verify an included MJCF model with:

```bash
uv run python scripts/smoke_mujoco.py assets/unitree_h1/mjcf/h1.xml --steps 1000
```

This headless smoke test loads the existing Unitree H1 model, advances MuJoCo's physics state, and checks finite joint position/velocity values. It does not validate an actuator policy or V10 trace adapter. The bundled H1 asset is attributed and licensed BSD-3-Clause in `assets/unitree_h1/README.md`.

## Defined craft completion (revision_08 feedback)

Requested flagship refinement now starts with a small set of observed weaknesses and completion criteria in the existing episode README. Director retains accepted beats and exposes inputs before a prediction/answer; Manim checks changing text through its transition; Blender diagnoses imported surfaces and checks cut entry/event/exit; finishing checks composed overlays; Reviewer records optional target results separately from technical, educational and learner evidence. Met targets reopen for regressions or changed scope, rather than an ever-expanding aesthetic standard.

Evidence: `pilots/05_moving_obstacle/revision_08/output/final_review.json` documents glyph-transition observations, imported facets/pastel paths, and corrected camera crop/occlusion. Those findings support targeted checks, not a claim of novice misunderstanding or creator parity. The earlier blocker/high-only instructions conflicted with requested craft refinement; they now permit defined craft targets and observations while preserving severity boundaries. No shared kit or episode renderer was changed by this skill update.

Tradeoff: inexpensive boundary/transition previews add focused review work before full rendering, while target completion limits unrelated redesign. Missing novice/playback evidence remains unverified, and required educational inspection cannot be marked PASS merely because the craft pass ends. Five skill folders pass `quick_validate.py`; review YAML parses; all 10 agent configurations pass `validate_codex_setup.py`; `git diff --check` passes. These validate instructions and wiring; effectiveness still needs application to newly rendered media.

## Linked discovery and studio craft (revision_09 follow-up)

The requested next upgrade strengthens two remaining craft directions: each inference should provide the next question's visible input, and physical detail shots should diagnose geometry/shading/light/framing separately. Director now audits adjacent discovery links without creating another beat list or lengthening a lesson by default; Manim carries the resolved relation into the next input; Blender compares a faithful surface/view candidate at the same solver pose; Reviewer states the specific benefit and its evidence. Accepted narration and bounded completion targets remain the starting point.

Evidence: R09's final review and README record successful local sentence replacement, corrected direction labels, stronger reference/actual contrast and remaining angular asset silhouettes. These support a narrower next craft comparison, not a claim that novice understanding failed or that creator parity was established. Existing kit angle smoothing means another smoothing instruction alone cannot repair a coarse silhouette. Reused B01 goal material states were made reproducible and checked against actual frame183; frame628 remained pixel-identical after the provenance patch.

Tradeoff: adjacent-link previews and same-state surface candidates add focused preparation, while preserving the single manifest, measured narration, solver geometry and defined stopping criteria. Shared kits and topics are unchanged. This skill-only follow-up does not rerender R09 or prove future narrative/surface improvement; the next requested production must supply that evidence. Format/wiring validation results are recorded after the checks below.

Validation of this follow-up: five skill folders pass `quick_validate.py`; review-template YAML parses; all 10 Codex agent configurations pass `validate_codex_setup.py`; `git diff --check` passes. No new render or learner evaluation was run for this instruction update.

## Reference-level mechanism update (2026-10-06)

bRd/3Blue1BrownKR 각4편의 공개 자료와 원본1080p 핵심 발췌를 조사했다. [조사·결정 근거](research/channel_craft_2026_10/STUDY.md), [검사 범위](research/channel_craft_2026_10/evidence.json)에 접근 한계까지 기록했다. Director는 같은 입력의 부품→도형→수식→응답을 설계하고, Manim은 표현 간 값/역할 대응을 보존하며, Blender는 충실한 부품의 작동 관계를 국소적으로 드러낸다. Finishing은 연결된 설명의 리듬을 보존하고 Reviewer는 여섯 비교 항목의 양쪽 증거를 기록한다.

스킬5개 형식,10개 에이전트 설정,리뷰 YAML 및8개 발췌 증거 경로/1080p/음성 검증 PASS. 공용 키트와 topics/기존 파일럿은 변경하지 않았다. 이번 변경은 제작 지침 개선이며 새 영상의 동급 판정은 아니다. 연속 재생·청취와 첫 이해의 검증은 다음 실제 렌더에서 남은 항목이다.

## R14 observed craft follow-up (2026-10-07)

User-requested skill refinement and push after R14 comparison. Actual final-frame observations support four targets: wheel close-ups have excess floor/small deciding parts; B05/B07/B09 prediction arrows cross redundant prompt text; B14 displacement bars leave distance-to-heading geometry weak; some formula transitions fragment intermediate glyphs. Director now selects task-led compositions and an explicitly ideal no-slip distance/angle construction. Blender frames the swept component/contact region. Manim preserves term objects and checks overlay sweeps. Reviewer verifies those same targets in composited frames and reports playback/listening separately.

Decision: narrow the next production to these observed gaps while retaining the accepted explanation, measured timing and physical evidence. Considered adding broad cinematic rules or increasing duration; neither addresses the named defects. Tradeoff: a focused geometric excerpt and same-state framing candidates require extra preview work. The ideal relation Δs=bθ is a teaching construction, not a new assertion about Bullet slip/contact. Existing single manifest and review report remain the interfaces. Missing helpers stay pilot-local while kits are protected.

Evidence: local `pilots/05_moving_obstacle/revision_14/output/final_review_report.json` and R14 README describe the inspected final and remaining scope. This skill change does not rerender R14, establish novice understanding or certify parity with reference creators. Prior pending viewer-feedback skill edits are retained in this skill commit; pending long-form validator and pilot artifacts are excluded. Validation: five involved skill folders pass `quick_validate.py`; all 10 agent configurations pass `uv run python scripts/validate_codex_setup.py`; `git diff --check` passes. These are format/wiring checks; effectiveness awaits the next rendered application.

## V10 MuJoCo arm environment and PoC (2026-10)

MuJoCo is now pinned in the project environment. `scripts/run_mujoco_arm_poc.py` executes a fixed-base, PD torque-controlled H1 arm run, records actual MuJoCo joint/body state to the existing V9 robotics trace format, and validates the hand pose through a separate forward-kinematics pass. `scripts/validate_mujoco_sensitivity.py` compares 2 ms and 1 ms physics steps. The resulting trace is rendered by the existing Manim renderer in `pilots/v10_mujoco_arm/`; it is a stylized trace visualization, not a Blender mesh render or narrated episode.

The run validates engine/model/trace/render connectivity. Contact counts and fixed-base/controller assumptions are recorded. Blender CLI and SoX are absent in the current WSL container; OS package installation is blocked by the container's `no new privileges` setting. The Three.js Phase 4 PoC now renders a 3D RAG embedding view in a managed Playwright Chromium browser and captures it to MP4. Remotion remains deferred because the fixed composition is covered by Three.js frame capture and FFmpeg without a React timeline. See the pilot READMEs for exact commands and limits.

## V11.5 execution and playback accuracy

H1 auto routing analyzes the whole joint trajectory, including return motion, with unit-specific noise thresholds. Its Blender overlay reports each motion phase's speed and marks holds explicitly. PID visuals now map each video frame to one recorded controller/encoder sample through the shared timeline, preserving discrete PWM and counts.

YOLO and MuJoCo now consult a validated execution cache before loading a model or integrating physics. Default storage is `output/executions/<topic>/<execution_id>/`; media stays in existing run directories. `--force` rerenders with reusable computation; `--force-execution` reruns computation into a preserved sibling; `--no-execution-cache` bypasses execution reuse. Small per-invocation reports record hit/miss and actual adapter calls. See [motion validation](docs/v11/V11_5_MOTION_VALIDATION.md), [cache contract](docs/v11/V11_5_EXECUTION_CACHE.md), and [measured results](docs/v11/V11_5_INTEGRATION_REPORT.md).
