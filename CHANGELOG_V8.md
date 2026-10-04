# V8 changes

- Added project-local Codex multi-agent routing under `.codex/`.
- Assigned model and reasoning effort per production stage.
- Added Astra-only escalation roles for Manim, Blender, deep review, and difficult paper research.
- Set low worker verbosity and compact handoff discipline to reduce output/context tokens.
- Added `AGENTS.md`, `MODEL_ROUTING.yaml`, `CODEX_SETUP.md`, and a config validator.
- Kept the working DaVinci MCP machine/user registration external; the bundle does not duplicate it.
