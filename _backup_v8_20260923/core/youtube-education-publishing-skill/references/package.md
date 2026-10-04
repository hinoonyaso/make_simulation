# Package + preflight

Create `publish/package.json`; paths are relative to that file.

```json
{
  "video": "../output/final.mp4",
  "title": "...",
  "description": "...",
  "privacy": "private",
  "captions": "../output/subtitles.ko.srt",
  "caption_language": "ko"
}
```

Optional: `thumbnail`, `channel_id`, `tags`, `publish_at`, `made_for_kids`, `contains_synthetic_media`, `chapters:[{seconds,title}]`.

Rules:
- title <= 100 characters; description <= 5000 UTF-8 bytes; neither may contain `<` or `>`.
- chapters come from the final edit timeline; captions must be timed SRT/VTT even if burned in.
- `publish_at` must be future, timezone-aware and paired with `privacy:"private"`; the bundled uploader currently rejects scheduling rather than silently publishing.
- missing channel/audience declarations may remain during local preparation but must be resolved before upload.

Run:
`python scripts/preflight.py publish/package.json`

Preflight is read-only: it checks package/media structure, audio+video streams, chapter bounds and hashes. It does not authorize, upload, fully decode, review visual content or validate remote eligibility.
