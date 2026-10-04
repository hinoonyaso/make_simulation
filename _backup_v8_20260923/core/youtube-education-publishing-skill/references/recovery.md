# Recovery / duplicate prevention

Use when a run was interrupted or the final API response is uncertain.

- Read receipt + private upload state before any new insert.
- If a resumable session exists, query server byte state and resume only from the acknowledged offset.
- If insertion may have completed, reconcile saved session/video ID and remote resources before creating anything new.
- Retry only transient network/429/5xx failures with bounded backoff; stop on auth/quota/permission changes.
- For captions, list tracks and reconcile language/name before inserting again; update/reuse the intended track rather than duplicating it.
- Never delete/reupload merely to fix title, description, thumbnail or captions.

A changed package/media hash invalidates automatic resume until manually reconciled.
