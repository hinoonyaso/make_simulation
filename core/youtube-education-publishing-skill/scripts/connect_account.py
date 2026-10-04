"""Connect a YouTube account via desktop OAuth; only reads channel information."""
import argparse
import json
import os
import tempfile
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Supports the intended video, subtitle and thumbnail publishing workflow.
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def callback_code(path, expected_state):
    parsed = urlsplit(path)
    query = parse_qs(parsed.query)
    states = query.get("state", [])
    if (parsed.path != "/" or len(states) != 1
            or not secrets.compare_digest(states[0], expected_state)):
        return None
    codes = query.get("code", [])
    if "error" in query or len(codes) != 1:
        return None
    return codes[0]


def login(flow, port):
    received = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log callback URLs containing authorization codes.

        def do_GET(self):
            code = callback_code(self.path, state)
            if code:
                received.append(code)
                message = "Authorization response received. You may close this tab. Channel verification is pending."
            else:
                message = "Old or incomplete login request. Close this tab and use the newest Google login link."
            self.send_response(200 if code else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(message.encode())

    with HTTPServer(("127.0.0.1", port), Handler) as server:
        flow.redirect_uri = f"http://localhost:{server.server_port}/"
        url, state = flow.authorization_url(prompt="consent", access_type="offline")
        print(f"OPEN_LOGIN_URL: {url}", flush=True)
        server.timeout = 1
        deadline = time.monotonic() + 1800
        while not received and time.monotonic() < deadline:
            server.handle_request()
        if not received:
            raise TimeoutError("Login expired")
    # State was checked before accepting the code. PKCE is handled by the flow.
    flow.fetch_token(code=received[0])
    return flow.credentials


def private_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".oauth-", dir=path.parent)
    try:
        try:
            os.chmod(name, 0o600)
        except OSError:
            pass  # Best effort on platforms without POSIX permission bits.
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(name, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path,
                        default=Path.home() / ".config/make_simulation/youtube")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--reauth", action="store_true")
    args = parser.parse_args()
    folder = args.config_dir.resolve()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        folder.chmod(0o700)
    except OSError:
        pass
    client = folder / "client_secret.json"
    if not client.is_file():
        raise FileNotFoundError(f"Missing OAuth desktop client: {client}")
    try:
        client.chmod(0o600)
    except OSError:
        pass
    config = json.loads(client.read_text(encoding="utf-8"))
    if "installed" not in config:
        raise ValueError("Desktop OAuth client required")
    installed = config["installed"]
    if installed.get("auth_uri") != "https://accounts.google.com/o/oauth2/auth":
        raise ValueError("Unexpected authorization endpoint")
    if installed.get("token_uri") != "https://oauth2.googleapis.com/token":
        raise ValueError("Unexpected token endpoint")
    token_path = folder / "token.json"
    credentials = None
    if token_path.exists() and not args.reauth:
        token_path.chmod(0o600)
        credentials = Credentials.from_authorized_user_file(str(token_path))
        if credentials.client_id != installed["client_id"]:
            raise ValueError("Stored token belongs to another client; use --reauth")
        if not credentials.has_scopes(SCOPES):
            raise ValueError("Stored token lacks required scope; use --reauth")
        if not credentials.valid and credentials.refresh_token:
            credentials.refresh(Request())
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_config(config, SCOPES,
                                                  autogenerate_code_verifier=True)
        credentials = login(flow, args.port)
    if not credentials.has_scopes(SCOPES) or not credentials.refresh_token:
        raise ValueError("Offline access and the requested permission are required")
    private_write(token_path, credentials.to_json())
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    result = youtube.channels().list(part="snippet", mine=True).execute()
    channels = [{"id": item["id"], "title": item["snippet"]["title"]}
                for item in result.get("items", [])]
    if not channels:
        raise ValueError("OAuth succeeded, but no YouTube channel was returned")
    private_write(folder / "channels.json", json.dumps(channels, ensure_ascii=False, indent=2))
    print(json.dumps({"connected_channels": channels, "uploaded": False},
                     ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # OAuth exceptions may contain callback codes or credentials; never print them.
        print(f"Connection failed ({type(exc).__name__}). Check consent, API enablement and local callback. Credentials were not printed.", flush=True)
        raise SystemExit(1)
