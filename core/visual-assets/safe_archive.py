"""Pinned, bounded archive download and extraction helpers.

This module never executes extracted files. Callers must supply a pinned hash,
declared size, HTTPS URL and an explicit host allowlist from reviewed metadata.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

MAX_ASSET_BYTES = 100 * 1024 * 1024
MAX_EXPANDED_BYTES = 1024 * 1024 * 1024

class _SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts): self.hosts = set(hosts)
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in self.hosts:
            raise urllib.error.HTTPError(newurl, code, "redirect host/scheme is not allowed", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def _safe_target(root: Path, name: str) -> Path:
    normalized = name.replace("\\", "/")
    rel = PurePosixPath(normalized)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or ":" in rel.parts[0]:
        raise ValueError(f"unsafe archive path: {name!r}")
    target = (root / Path(*rel.parts)).resolve()
    if not target.is_relative_to(root.resolve()): raise ValueError(f"archive path escapes staging: {name!r}")
    return target

def safe_extract_archive(archive: Path, destination: Path, *, max_expanded_bytes=MAX_EXPANDED_BYTES) -> None:
    if destination.is_symlink(): raise ValueError("extraction destination symlinks are not allowed")
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve(); total = 0
    def copy_member(name, stream, size):
        nonlocal total
        total += size
        if total > max_expanded_bytes: raise ValueError("archive expanded size limit exceeded")
        target = _safe_target(root, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output: shutil.copyfileobj(stream, output)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as bundle:
            for info in bundle.infolist():
                target = _safe_target(root, info.filename)
                mode = info.external_attr >> 16
                if mode & 0o170000 == 0o120000: raise ValueError(f"archive symlink is not allowed: {info.filename}")
                if info.is_dir(): target.mkdir(parents=True, exist_ok=True); continue
                with bundle.open(info) as stream: copy_member(info.filename, stream, info.file_size)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive, "r:*") as bundle:
            for member in bundle.getmembers():
                target = _safe_target(root, member.name)
                if member.isdir(): target.mkdir(parents=True, exist_ok=True); continue
                if not member.isfile(): raise ValueError(f"archive links/special files are not allowed: {member.name}")
                stream = bundle.extractfile(member)
                if stream is None: raise ValueError(f"cannot read archive member: {member.name}")
                with stream: copy_member(member.name, stream, member.size)
    else: raise ValueError("only ZIP and TAR archives are supported")

def fetch_pinned_archive(*, url: str, destination: str | Path, sha256: str,
                         size_bytes: int, allowed_hosts: list[str], allow_large=False) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname not in set(allowed_hosts):
        raise ValueError("archive URL must use HTTPS and a declared host")
    if len(sha256) != 64 or any(char not in "0123456789abcdefABCDEF" for char in sha256):
        raise ValueError("a pinned SHA-256 is required")
    if not isinstance(size_bytes, int) or size_bytes <= 0: raise ValueError("a positive declared archive size is required")
    if size_bytes > MAX_ASSET_BYTES and not allow_large:
        raise ValueError(f"archive is {size_bytes} bytes; assets above 100 MiB require explicit approval")
    target = Path(destination).resolve(); target.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = target / ".asset_source.json"
    if target.is_dir() and metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (metadata.get("archive_sha256") == sha256.lower() and
                metadata.get("content_sha256") == _tree_hash(target)):
            return {"status":"cache_hit", "destination":str(target), "sha256":sha256}
    stage = Path(tempfile.mkdtemp(prefix="asset-fetch-", dir=target.parent)); archive = stage / "source.archive"
    try:
        opener = urllib.request.build_opener(_SameHostRedirect(allowed_hosts))
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent":"make_simulation-asset-fetch/1"})
        with opener.open(request, timeout=20) as response:
            header_size = response.headers.get("Content-Length")
        if header_size is not None and int(header_size) != size_bytes: raise ValueError("archive size differs from pinned metadata")
        digest = hashlib.sha256(); received = 0
        with opener.open(urllib.request.Request(url, headers={"User-Agent":"make_simulation-asset-fetch/1"}), timeout=60) as response, archive.open("wb") as out:
            while block := response.read(1024*1024):
                received += len(block)
                if received > size_bytes or (received > MAX_ASSET_BYTES and not allow_large): raise ValueError("download exceeded permitted size")
                digest.update(block); out.write(block)
        if received != size_bytes or digest.hexdigest().lower() != sha256.lower():
            raise ValueError("download size or SHA-256 does not match pinned metadata")
        unpacked = stage / "unpacked"; safe_extract_archive(archive, unpacked)
        if (unpacked / ".asset_source.json").exists(): raise ValueError("archive contains reserved metadata filename")
        content_hash = _tree_hash(unpacked)
        (unpacked / ".asset_source.json").write_text(json.dumps({"archive_sha256":digest.hexdigest(),
            "content_sha256":content_hash,"source_url":url,"size_bytes":received}, indent=2)+"\n", encoding="utf-8")
        if target.exists(): raise FileExistsError(f"refusing to replace existing asset directory: {target}")
        os.replace(unpacked, target)
        return {"status":"downloaded_and_hash_verified", "destination":str(target), "sha256":digest.hexdigest(), "size_bytes":received}
    finally:
        shutil.rmtree(stage, ignore_errors=True)

def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    if root.is_symlink(): raise ValueError("cached asset directory symlink is not allowed")
    paths = sorted(root.rglob("*"))
    if any(path.is_symlink() for path in paths): raise ValueError("cached asset contains a symlink")
    for path in (p for p in paths if p.is_file() and p.relative_to(root).as_posix() != ".asset_source.json"):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024*1024), b""): digest.update(block)
    return digest.hexdigest()
