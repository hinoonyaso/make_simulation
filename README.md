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
