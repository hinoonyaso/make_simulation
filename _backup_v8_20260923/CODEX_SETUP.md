# Codex setup

## Use
1. Extract this bundle and `cd` into the bundle root (or copy `.codex/`, `AGENTS.md`, `ROUTING.md`, `MODEL_ROUTING.yaml`, `core/`, and `optional/` into your project root).
2. Start Codex in that trusted project.
3. Run `/status` and verify the project-local config is loaded.
4. The main orchestrator uses Terra/medium and delegates to custom roles automatically when appropriate.

Project-local config is under `.codex/config.toml`; agent model/effort files are under `.codex/agents/`.

## Design intent
- Terra/Luna handle routine, bounded work.
- Sol/high handles story, Manim/Blender normal generation, review, and normal paper analysis.
- Astra/high is escalation-only for hero visuals, hard review failures, or difficult research.
- Worker verbosity is low to reduce output tokens; quality comes from the selected reasoning effort and real-render verification.

## Existing MCPs
Do not duplicate machine-level MCP registration here. The Resolve role expects the already-working `davinci-resolve` MCP to be available from your user/global Codex configuration.

## Manual override
Codex CLI flags/project config override the defaults if you deliberately choose a different model or effort. If an account/workspace does not expose Astra, use the normal Sol role instead.
