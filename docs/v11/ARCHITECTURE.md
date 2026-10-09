# V11 architecture

V11 adds an import-light capability catalog, a small `MechanismAdapter` Protocol, lazy adapter loading, and one production CLI. Existing trace schemas remain in domain payloads; `mechanism-envelope/v1` adds execution provenance and limitations around new numerical adapters. RAG delegates to V10, while the H1 adapter delegates to the existing MuJoCo runner. V9 manifest generation and Manim delivery validation are reused.

Flow: topic/alias → capability lookup → adapter `prepare/execute/validate` → trace-backed visual plan → V9-compatible manifest → Manim renderer → full decode validation. A topic is executable only when its registry override names a ready adapter. All other catalog rows are planned and fail explicitly.

Adapters are loaded only after lookup so catalog inspection does not require MuJoCo, Manim, or model runtimes. Domain traces are not converted into one shared payload schema. Asset resolution stays local and converter injection remains explicit.

This is a technical silent-render path. Narration, captions, render-reviewer evidence, and V9 final delivery are not automatically completed by the V11 CLI. See [capability matrix](CAPABILITY_MATRIX.md) and [limitations](LIMITATIONS.md).
