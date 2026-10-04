# Resolve edit safety

Read only before destructive cleanup, ripple edits, replacement, deletion, or project-level operations.

- Never delete or overwrite the only master timeline.
- Snapshot/duplicate the timeline before destructive passes.
- Prefer dry-run/proposal actions when available.
- Inspect item identities before clip-specific operations.
- Do not change project-wide settings merely to fix one clip unless explicitly required.
- Do not remove source media from disk.
- Do not delete projects/databases/presets unless the user explicitly requests it.
- If an operation is irreversible or the MCP marks it high-risk, require explicit user intent and use the MCP's safety/confirmation mechanism.
