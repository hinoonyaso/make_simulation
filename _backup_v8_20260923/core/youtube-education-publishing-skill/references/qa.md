# Remote QA + completion

After upload, verify rather than infer:
- returned video belongs to intended channel;
- requested privacy/schedule state;
- upload/processing/failure status;
- intended caption track status;
- thumbnail attachment when requested.

Poll with a bounded deadline; if processing is unfinished, report `processing/pending` rather than success.

`publish/receipt.json` should contain only: package/media hashes, channel/video/caption IDs, requested + observed states, timestamps, and completed/pending operations. Never include OAuth secrets, bearer tokens or resumable URLs.

Final report: `video ID/link | observed visibility | processing | captions | thumbnail | unfinished work`.
