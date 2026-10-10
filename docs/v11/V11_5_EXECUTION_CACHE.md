# V11.5 execution and render caches

## Decision and scope

The expensive YOLO/H1 execution used to precede the first cache lookup. `core/mechanism/execution_cache.py` now reserves and validates computation independently:

Request → normalized input + content hashes → execution reservation/cache → validated trace → renderer preflight → timeline → render cache → media.

The existing adapter interface and V9/V10 trace schemas remain intact. The execution cache currently serves `object_detection` and fixed-base `robot_kinematics`. Cheap numerical adapters still execute normally; explicit replay bypasses execution. This limited implementation avoids a new framework and preserves all old run directories.

## Execution identity

Identity includes topic, cache schema/adapter version, normalized execution options, relevant execution source hashes, runtime versions, and source content hashes. Absolute image/model locations and temporary output directories are excluded from identity. On a cache hit, original trace bytes and provenance hashes are checked before rebinding source path fields to the current identical-content files; cached originals are not changed.

- YOLO: image/checkpoint SHA-256, confidence/IoU/display floor/image size/display limit, Ultralytics/Torch/Torchvision/Pillow/OpenCV/Numpy/Python versions, CPU/float32/rect=False/max_det=300/class-aware NMS and fixed seed 0. Unsupported options are rejected. `imgsz` and display floor now actually reach the child inference command.
- H1: MJCF SHA-256 plus complete existing bundle hash, duration/timestep/sample period, MuJoCo/Numpy/Python versions. Solver and inertial/mesh configuration are covered by MJCF/bundle bytes. Fixed initial state, PD constants and target trajectory are covered by the simulation implementation fingerprint. Unsupported controller/solver/trajectory override keys are rejected rather than silently ignored.
- Runtime identity also includes platform/machine. A changed runtime means a different execution key. Cache hits do not import/load the detector or run physics, but still hash files and validate trace equations/provenance.

Manim/Blender scene, timeline and presentation edits are excluded from the execution fingerprint. Render identity still conservatively fingerprints the render pipeline and its adapter dependencies; this can rerender after an adapter edit even when returned values match, but it never causes a scene-only edit to rerun YOLO or MuJoCo.

## Storage and concurrency

Default execution storage: `output/executions/<topic>/<execution_id>/`. Each reservation contains `request.json` (identity, normalized config, source/runtime provenance), `trace.json`, and `execution_report.json` with status, identity, SHA-256 and timings. Files are written to same-directory temporary files, flushed/fsynced, then atomically renamed. The final `COMPLETE` record is written last.

A process-level `flock` on a per-identity file serializes lookup/execution/promotion on Linux/WSL. A waiting process gets the successful first result instead of executing twice. A 120-second reservation timeout is explicit. Kernel locks release when a process crashes; no PID-age guessing or unsafe stale-lock deletion is used. Interrupted/incomplete directories are retained and **rejected**, with instructions to force an independent run. Forced runs use unique sibling directories and preserve successful originals. Network filesystems and native Windows locking are not validated.

Every hit checks completion, schema/identity, stored trace byte hash, source/model provenance and domain-specific validation. Sources are rehashed before promotion to reject ordinary concurrent input changes. This is a correctness cache, not a defence against a privileged adversary rewriting both data and manifests.

## CLI behaviour and reporting

```bash
# Default: independently reuse valid execution and media.
uv run python scripts/produce_video.py --topic robot_kinematics --preview
# Rerender while keeping validated computation.
uv run python scripts/produce_video.py --topic robot_kinematics --preview --force
# Rerun computation into an independent sibling; render may still reuse equal results.
uv run python scripts/produce_video.py --topic robot_kinematics --preview --force-execution
# Bypass execution reuse, retaining an independent execution record.
uv run python scripts/produce_video.py --topic robot_kinematics --preview --no-execution-cache
```

`--execution-cache-dir` selects storage for experiments. Existing `--reuse/--no-reuse`, `--force` and `--run-id` keep their render-directory semantics. `--force` does not now imply force-execution. `--force-execution --force` reruns both stages.

A first production report records execution provenance. Each invocation also writes a small immutable `<output-dir>/invocations/<time_ns>.json` with execution HIT/MISS/FORCED/DISABLED, actual adapter call count, render HIT/MISS and measured timings. This prevents a cache hit from overwriting the original production evidence or falsely reporting the original MISS as the current invocation's result.

`model_loading_sec` is YOLO constructor time (runtime imports remain part of adapter duration), or MuJoCo model compilation time. Cache-hit model loading and adapter calls are zero. Hashing, trace validation, preflight, render lookup/full decode, render and total pipeline time remain visible. One-shot local timings are observations, not a hardware-independent benchmark or speedup guarantee.
