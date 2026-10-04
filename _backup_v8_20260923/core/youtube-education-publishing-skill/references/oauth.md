# OAuth account connection

Use user OAuth, not an API key, for upload/caption management.

Place a Google Desktop OAuth client at:
`~/.config/make_simulation/youtube/client_secret.json`

Run:
`python scripts/connect_account.py`

The script opens a localhost callback, checks OAuth state + PKCE, stores credentials outside the repo, and verifies the connected YouTube channel without uploading. Use `--reauth` only to intentionally change account.

The configured `youtube.force-ssl` scope is broader than the read-only connection step because later video/caption operations need it. Never expose tokens, callback codes or client secrets in chat/logs. Compare the returned channel ID with the intended upload channel before mutation.
