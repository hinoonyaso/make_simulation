---
name: youtube-education-publishing-skill
version: 2.0
description: Low-token, high-reliability YouTube preparation and authorized publishing for educational videos: package/preflight, OAuth, resumable upload, captions/thumbnail, recovery and remote verification.
---

# YouTube Education Publishing

Use only after a final video exists. Preparing a package is **not** authorization to upload. Do not preload all references.

## Route on demand

- metadata/package/preflight only -> `references/package.md`
- connect or change Google account -> `references/oauth.md`
- authorized upload -> `references/execute.md`
- interrupted/uncertain/duplicate-risk run -> `references/recovery.md`
- processing/status/final publication check -> `references/qa.md`

## Core rules

1. Select the exact final artifact from the production handoff; verify path/version/hash rather than trusting a `final` filename.
2. Preserve research truth: title/thumbnail/description cannot outrun verified claims; disclose toy/simulated/local results accurately.
3. Never infer `made_for_kids` or realistic synthetic-media disclosure. Resolve required execution fields before mutation.
4. Before every mutation, read `publish/receipt.json` and local state. After an uncertain insert/upload response, **reconcile before retrying**; never create a duplicate video to fix metadata/captions.
5. Keep OAuth tokens, client secrets and resumable URLs outside repo/receipt. Never ask users to paste credentials in chat.
6. Upload only when channel, artifact and requested visibility/publication action are already authorized in the session. Otherwise finish the reviewable local package first.
7. Treat `uploaded`, `processing`, `scheduled`, and `public` as different states; verify remote state before reporting completion.

## Default flow

`final render -> package -> preflight -> authorization/channel check -> resumable upload -> captions/thumbnail -> remote verify -> receipt`

Prefer an existing upload-capable connector when available; otherwise use the bundled YouTube Data API scripts. Do not copy API documentation into context—open only the active reference.
