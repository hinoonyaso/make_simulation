#!/usr/bin/env python3
"""Create a disclosed 3D PCA display projection from the real RAG vectors."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
TRACE_PATH = ROOT / "pilots/v10_rag_poc/data/ai_trace.json"
OUT = Path(__file__).resolve().parents[1] / "data/embedding_space_3d.json"


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    trace = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
    errors = module.validate_trace(trace)
    if errors:
        raise SystemExit("invalid AI trace: " + "; ".join(errors))
    vectors = [item for item in trace["intermediate_values"] if item["kind"] == "embedding"]
    query = next(item for item in trace["inputs"] if item.get("kind") == "query")
    ids = [item["id"].removeprefix("vector:") for item in vectors] + [query["id"]]
    matrix = np.asarray([item["value"] for item in vectors] + [query["embedding"]], dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != 384 or not np.isfinite(matrix).all():
        raise SystemExit(f"expected finite 384-dimensional vectors, got {matrix.shape}")
    centered = matrix - matrix.mean(axis=0)
    _, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
    components = vt[:3].copy()
    coordinates = centered @ components.T
    # Fix arbitrary SVD signs deterministically for comparable rerenders.
    for axis in range(3):
        anchor = int(np.argmax(np.abs(components[axis])))
        if components[axis, anchor] < 0:
            components[axis] *= -1
            coordinates[:, axis] *= -1
    maximum = float(np.abs(coordinates).max())
    if maximum > 0:
        coordinates *= 3.4 / maximum
    variance = singular_values ** 2
    ratios = variance[:3] / variance.sum()
    top_ids = trace["outputs"][0]["retrieved_ids"]
    ranks = {chunk_id: rank for rank, chunk_id in enumerate(top_ids, start=1)}
    output = {
        "schema": "ai-embedding-display-projection/v1",
        "source_trace_sha256": hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest(),
        "method": "PCA by deterministic NumPy SVD over 11 stored chunk vectors and the stored query vector",
        "source_dimension": int(matrix.shape[1]),
        "display_dimension": 3,
        "explained_variance_ratio": ratios.tolist(),
        "projection_is_lossy": True,
        "geometry_semantics": "display coordinates only; retrieval rankings and distances remain from original 384D vectors",
        "retrieval": {"metric": "squared L2", "top_k_ids": top_ids,
                      "scores_and_ranks_source": "ai_trace.json"},
        "points": [{"id": item_id, "xyz": coordinates[i].tolist(),
                    "rank": ranks.get(item_id), "kind": "query" if item_id == query["id"] else "chunk"}
                   for i, item_id in enumerate(ids)],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(vectors)} vectors + query projected from 384D to 3D; "
          f"PCA variance {ratios.sum():.4f}; top3={','.join(top_ids)}")
    print(OUT)


if __name__ == "__main__":
    main()
