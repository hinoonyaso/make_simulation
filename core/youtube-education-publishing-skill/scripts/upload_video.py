"""Upload a reviewed package; preserve session/video IDs across interruptions."""
import argparse
import hashlib
import json
import mimetypes
import os
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from connect_account import private_write
from preflight import check


def save(path, value):
    private_write(path, json.dumps(value, ensure_ascii=False, indent=2))


def offset(response):
    value = response.headers.get("Range")
    return int(value.rsplit("-", 1)[1]) + 1 if value else 0


@contextmanager
def exclusive_lock(path):
    """Non-blocking one-byte lock for Windows and POSIX."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    try:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("Another upload process is using this package") from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError("Another upload process is using this package") from exc
        yield
    finally:
        try:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        stream.close()


def transfer(session, url, video, mime):
    """Reconcile server state before sending/resending bytes."""
    total = video.stat().st_size
    for attempt in range(6):
        try:
            r = session.put(url, headers={"Content-Range": f"bytes */{total}"},
                            data=b"", timeout=120)
            if r.status_code in (200, 201):
                return r.json()
            if r.status_code != 308:
                r.raise_for_status()
                raise RuntimeError("Unexpected resumable status")
            start = offset(r)
            with video.open("rb") as stream:
                stream.seek(start)
                while start < total:
                    block = stream.read(4 * 1024 * 1024)
                    if not block:
                        raise RuntimeError("Unexpected end of media")
                    end = start + len(block) - 1
                    r = session.put(url, data=block, timeout=180, headers={
                        "Content-Type": mime,
                        "Content-Range": f"bytes {start}-{end}/{total}"})
                    if r.status_code in (200, 201):
                        return r.json()
                    if r.status_code != 308:
                        r.raise_for_status()
                        raise RuntimeError("Unexpected upload response")
                    next_byte = offset(r)
                    if not start < next_byte <= start + len(block):
                        raise RuntimeError("Invalid acknowledged range")
                    start = next_byte
                    stream.seek(start)
                    print(f"Upload {start}/{total} bytes", flush=True)
        except Exception as exc:
            import requests
            if not isinstance(exc, (requests.ConnectionError, requests.Timeout, requests.HTTPError)):
                raise
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status is not None and status not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"Upload HTTP {status}; saved session retained") from None
            if attempt == 5:
                raise RuntimeError("Upload interrupted; resume using saved session") from None
            delay = min(2 ** attempt, 32)
            retry_after = getattr(getattr(exc, "response", None), "headers", {}).get("Retry-After", "")
            if retry_after.isdigit():
                if int(retry_after) > 60:
                    raise RuntimeError("Retry-After exceeds current wait budget; resume later") from None
                delay = max(delay, int(retry_after))
            time.sleep(delay)
    raise RuntimeError("Resumable session incomplete")


def execute(package, config_dir=None):
    package = Path(package).resolve()
    report = check(package)
    data = json.loads(package.read_text(encoding="utf-8"))
    if not data.get("channel_id") or type(data.get("made_for_kids")) is not bool:
        raise ValueError("channel_id and made_for_kids required")
    if "publish_at" in data:
        raise ValueError("This uploader does not yet support scheduling")

    folder = Path(config_dir or Path.home() / ".config/make_simulation/youtube").resolve()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        folder.chmod(0o700)
    except OSError:
        pass

    key = hashlib.sha256((data["channel_id"] + report["sha256"]["video"]).encode()).hexdigest()
    state_path = folder / f"upload-{key}.json"
    with exclusive_lock(folder / f"upload-{key}.lock"):
        run_locked(package, data, report, folder, state_path)


def run_locked(package, data, report, folder, state_path):
    token = folder / "token.json"
    if not token.is_file():
        raise FileNotFoundError(f"Missing OAuth token: {token}; run connect_account.py first")
    creds = Credentials.from_authorized_user_file(str(token))
    if not creds.valid:
        creds.refresh(Request())
        private_write(token, creds.to_json())

    api = build("youtube", "v3", credentials=creds, cache_discovery=False)
    channels = api.channels().list(part="id", mine=True).execute().get("items", [])
    if data["channel_id"] not in [c["id"] for c in channels]:
        raise ValueError("Authenticated channel does not match package")

    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    receipt_path = package.parent / "receipt.json"
    if state and state.get("hashes") != report["sha256"]:
        raise ValueError("Package changed since upload started; reconcile before retrying")
    state.update(hashes=report["sha256"], channel_id=data["channel_id"])

    def checkpoint():
        save(state_path, state)
        save(receipt_path, {k: v for k, v in state.items() if k != "session_url"})

    video = (package.parent / data["video"]).resolve()
    mime = mimetypes.guess_type(video.name)[0] or "application/octet-stream"
    if not (mime.startswith("video/") or mime == "application/octet-stream"):
        raise ValueError(f"Unexpected video MIME type: {mime}")
    session = AuthorizedSession(creds)

    if not state.get("video_id"):
        if not state.get("session_url"):
            if state.get("init_started"):
                raise RuntimeError("Uncertain session creation; inspect saved state before another insert")
            state["init_started"] = True
            checkpoint()
            body = {
                "snippet": {
                    "title": data["title"], "description": data["description"],
                    "tags": data.get("tags", []), "categoryId": "27",
                    "defaultLanguage": "ko", "defaultAudioLanguage": "ko"
                },
                "status": {
                    "privacyStatus": data["privacy"],
                    "selfDeclaredMadeForKids": data["made_for_kids"]
                }
            }
            if "contains_synthetic_media" in data:
                body["status"]["containsSyntheticMedia"] = data["contains_synthetic_media"]
            r = session.post(
                "https://www.googleapis.com/upload/youtube/v3/videos",
                params={"uploadType": "resumable", "part": "snippet,status"},
                json=body,
                headers={"X-Upload-Content-Type": mime,
                         "X-Upload-Content-Length": str(video.stat().st_size)},
                timeout=60)
            if r.status_code != 200:
                raise RuntimeError(f"Upload initialization HTTP {r.status_code}")
            url = r.headers["Location"]
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.hostname != "www.googleapis.com":
                raise RuntimeError("Unexpected upload endpoint")
            state["session_url"] = url
            checkpoint()

        result = transfer(session, state["session_url"], video, mime)
        state["video_id"] = result["id"]
        checkpoint()
        print("Video uploaded:", state["video_id"], flush=True)

    vid = state["video_id"]
    if data.get("captions") and not state.get("caption_id"):
        name = "한국어 · 대본 교정"
        tracks = api.captions().list(part="snippet", videoId=vid).execute().get("items", [])
        existing = [t for t in tracks if t["snippet"].get("name") == name
                    and t["snippet"].get("language") == data["caption_language"]]
        if existing:
            state["caption_id"] = existing[0]["id"]
        else:
            if state.get("caption_started"):
                raise RuntimeError("Caption response uncertain; no duplicate track inserted")
            state["caption_started"] = True
            checkpoint()
            result = api.captions().insert(
                part="snippet",
                body={"snippet": {"videoId": vid, "language": data["caption_language"],
                                  "name": name, "isDraft": False}},
                media_body=MediaFileUpload(str(package.parent / data["captions"]),
                                           mimetype="application/octet-stream")
            ).execute()
            state["caption_id"] = result["id"]
        checkpoint()

    if data.get("thumbnail") and not state.get("thumbnail_done"):
        api.thumbnails().set(videoId=vid, media_body=MediaFileUpload(
            str(package.parent / data["thumbnail"]))).execute()
        state["thumbnail_done"] = True
        checkpoint()

    for _ in range(30):
        items = api.videos().list(part="snippet,status,processingDetails", id=vid).execute().get("items", [])
        if not items:
            raise RuntimeError("Uploaded video not returned by videos.list")
        remote = items[0]
        if remote["snippet"]["channelId"] != data["channel_id"]:
            raise RuntimeError("Remote video channel mismatch")
        state["remote_status"] = remote["status"]
        state["processing"] = remote.get("processingDetails", {}).get("processingStatus")
        if state.get("caption_id"):
            cap = api.captions().list(part="snippet", id=state["caption_id"], videoId=vid).execute()
            state["caption_status"] = cap.get("items", [{}])[0].get("snippet", {}).get("status")
        checkpoint()
        if state["processing"] != "processing" and state.get("caption_status") != "syncing":
            break
        print("Waiting for YouTube processing…", flush=True)
        time.sleep(10)

    print(json.dumps({
        "video_id": vid,
        "status": state.get("remote_status"),
        "processing": state.get("processing"),
        "caption_status": state.get("caption_status"),
        "thumbnail_done": state.get("thumbnail_done")
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--config-dir", type=Path)
    args = parser.parse_args()
    try:
        execute(args.package, args.config_dir)
    except Exception as exc:
        from googleapiclient.errors import HttpError
        if isinstance(exc, HttpError):
            try:
                error = json.loads(exc.content).get("error", {})
                reasons = [e.get("reason") for e in error.get("errors", [])]
            except Exception:
                reasons = []
            print("YouTube API error:", exc.resp.status, reasons, flush=True)
        elif isinstance(exc, (ValueError, RuntimeError, FileNotFoundError)):
            print(str(exc), flush=True)
        else:
            print("Upload stopped:", type(exc).__name__, "; saved state retained", flush=True)
        raise SystemExit(1)
