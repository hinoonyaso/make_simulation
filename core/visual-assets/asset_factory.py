"""Safe local asset resolver and content-addressed conversion cache.

Network download and format conversion are injected capabilities; this module does
not silently install tools or download unreviewed models.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable


REQUIRED = {"id", "tool", "kind", "source", "version", "assumptions", "semantic_role", "provenance"}


class AssetFactory:
    def __init__(self, root: str | Path, registry: str | Path | None = None,
                 cache: str | Path | None = None):
        self.root = Path(root).resolve()
        self.registry_path = Path(registry or self.root / "core/visual-assets/registry.json").resolve()
        self.cache_root = Path(cache or self.root / ".cache/visual-assets").resolve()

    def _registry(self) -> dict:
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if not isinstance(data.get("assets"), list):
            raise ValueError("registry assets must be a list")
        return data

    def _entry(self, asset_id: str) -> dict:
        matches = [row for row in self._registry()["assets"] if row.get("id") == asset_id]
        if len(matches) != 1:
            raise KeyError(f"asset id must resolve uniquely: {asset_id}")
        return matches[0]

    def resolve_asset(self, asset_id: str) -> Path:
        entry = self._entry(asset_id)
        path = (self.root / entry["source"]).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("asset source escapes project root")
        return path

    @staticmethod
    def _hash_path(path: Path) -> str:
        digest = hashlib.sha256()
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        if not files:
            raise ValueError(f"asset has no files: {path}")
        for item in files:
            rel = item.name if path.is_file() else item.relative_to(path).as_posix()
            digest.update(rel.encode("utf-8") + b"\0")
            with item.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
        return digest.hexdigest()

    def validate_asset(self, asset_id: str) -> dict:
        entry = self._entry(asset_id)
        path = self.resolve_asset(asset_id)
        if not path.exists():
            raise FileNotFoundError(path)
        digest = self._hash_path(path)
        declared = entry.get("source_sha256")
        if declared and declared != digest:
            raise ValueError(f"source hash mismatch for {asset_id}")
        return {"asset_id": asset_id, "path": str(path), "sha256": digest,
                "file_count": 1 if path.is_file() else sum(1 for p in path.rglob("*") if p.is_file()),
                "license": entry.get("license"), "validation": "local_files_present"}

    def _cache_key(self, asset_id: str, source_hash: str, target: str) -> str:
        entry = self._entry(asset_id)
        payload = {"asset_id": asset_id, "source_sha256": source_hash,
                   "target_format": target.lower(), "source_revision": entry.get("source_commit"),
                   "factory_version": 1}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def get_cached_asset(self, asset_id: str, target_format: str) -> Path | None:
        report = self.validate_asset(asset_id)
        key = self._cache_key(asset_id, report["sha256"], target_format)
        folder = self.cache_root / asset_id / key
        meta_path = folder / "asset.json"
        if not meta_path.is_file():
            return None
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        artifact = folder / meta.get("artifact", "")
        if (meta.get("source_sha256") != report["sha256"] or
                meta.get("target_format") != target_format.lower() or not artifact.is_file()):
            return None
        if self._hash_path(artifact) != meta.get("artifact_sha256"):
            return None
        return artifact

    def convert_asset(self, asset_id: str, target_format: str,
                      converter: Callable[[Path, Path, dict], Path] | None = None) -> Path:
        cached = self.get_cached_asset(asset_id, target_format)
        if cached:
            return cached
        if converter is None:
            raise RuntimeError(f"no converter configured for {target_format}; source is retained")
        entry = self._entry(asset_id)
        source = self.resolve_asset(asset_id)
        source_hash = self.validate_asset(asset_id)["sha256"]
        key = self._cache_key(asset_id, source_hash, target_format)
        self.cache_root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix="asset-convert-", dir=self.cache_root))
        try:
            result = Path(converter(source, staging, entry)).resolve()
            if not result.is_relative_to(staging.resolve()) or not result.is_file():
                raise ValueError("converter must return a file inside its staging directory")
            artifact_hash = self._hash_path(result)
            destination = self.cache_root / asset_id / key
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                shutil.rmtree(destination)
            os.replace(staging, destination)
            relative = result.relative_to(staging).as_posix()
            metadata = {"asset_id": asset_id, "source_sha256": source_hash,
                        "target_format": target_format.lower(), "artifact": relative,
                        "artifact_sha256": artifact_hash, "source_revision": entry.get("source_commit")}
            (destination / "asset.json").write_text(json.dumps(metadata, indent=2) + "\n")
            return destination / relative
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    def register_asset(self, metadata: dict) -> None:
        missing = REQUIRED - set(metadata)
        if missing:
            raise ValueError(f"missing asset metadata: {sorted(missing)}")
        if not isinstance(metadata["version"], (str, int)):
            raise ValueError("version must be a string or integer")
        data = self._registry()
        if any(row.get("id") == metadata["id"] for row in data["assets"]):
            raise ValueError(f"duplicate asset id: {metadata['id']}")
        data["assets"].append(metadata)
        tmp = self.registry_path.with_suffix(self.registry_path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.registry_path)

    def invalidate_asset_cache(self, asset_id: str) -> bool:
        self._entry(asset_id)
        folder = self.cache_root / asset_id
        if not folder.exists():
            return False
        if not folder.resolve().is_relative_to(self.cache_root):
            raise ValueError("cache path escapes cache root")
        shutil.rmtree(folder)
        return True
