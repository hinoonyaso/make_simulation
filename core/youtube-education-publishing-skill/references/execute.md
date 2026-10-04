# Authorized upload

At execution time, verify current official YouTube Data API docs for `videos.insert`, resumable upload, `videos/status`, captions and thumbnails.

Before upload:
- rerun preflight;
- compare package/media hashes with the reviewed artifact and existing receipt/state;
- verify authenticated channel and requested privacy;
- confirm required audience/disclosure fields.

Run:
`python scripts/upload_video.py publish/package.json`

The bundled uploader:
- starts/persists one resumable session;
- reconciles acknowledged bytes before sending;
- stores video ID immediately;
- attaches one intended timed caption track and thumbnail when provided;
- polls remote processing with a bounded wait;
- writes a receipt without secrets/session URL.

Scheduling is deliberately rejected by this client until explicitly implemented. Metadata/visibility changes on an existing video require a separate authorized update flow that first fetches and preserves writable fields.
