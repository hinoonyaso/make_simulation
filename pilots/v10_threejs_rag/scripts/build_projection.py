#!/usr/bin/env python3
"""Create a disclosed 3D PCA display projection from the real RAG vectors."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
TRACE_PATH = Path(os.environ.get("V10_AI_TRACE", ROOT / "pilots/v10_rag_poc/data/ai_trace.json")).resolve()
OUT = Path(os.environ.get("V10_THREE_PROJECTION", Path(__file__).resolve().parents[1] / "data/embedding_space_3d.json"))


def project_matrix(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Project finite rows deterministically; constant data yields zero variance safely."""
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 1 or not np.isfinite(matrix).all():
        raise ValueError(f"expected at least two finite vectors with one dimension, got {matrix.shape}")
    centered = matrix - matrix.mean(axis=0)
    _, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
    components = vt[:3].copy()
    coordinates = centered @ components.T
    if coordinates.shape[1] < 3:
        coordinates = np.pad(coordinates, ((0, 0), (0, 3-coordinates.shape[1])))
    for axis in range(min(3, len(components))):
        anchor = int(np.argmax(np.abs(components[axis])))
        if components[axis, anchor] < 0:
            components[axis] *= -1
            coordinates[:, axis] *= -1
    maximum = float(np.abs(coordinates).max())
    if maximum > 0:
        coordinates *= 3.4 / maximum
    variance = singular_values ** 2
    total_variance = float(variance.sum())
    ratios = (np.pad(variance[:3] / total_variance, (0, max(0, 3-len(variance[:3]))))
              if total_variance > np.finfo(np.float64).eps else np.zeros(3, dtype=np.float64))
    return coordinates, ratios


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    trace = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
    errors = module.validate_trace(trace)
    if errors:
        raise SystemExit("invalid AI trace: " + "; ".join(errors))
    vectors = [item for item in trace["intermediate_values"]
               if item["kind"] in {"embedding", "feature_vector"}]
    query = next(item for item in trace["inputs"] if item.get("kind") == "query")
    query_vector = query.get("embedding", query.get("features"))
    ids = [item.get("source_id", item["id"].removeprefix("vector:")) for item in vectors] + [query["id"]]
    matrix = np.asarray([item["value"] for item in vectors] + [query_vector], dtype=np.float64)
    if not vectors or matrix.ndim != 2 or matrix.shape[1] < 1 or not np.isfinite(matrix).all():
        raise SystemExit(f"expected finite, dimension-matched recorded vectors, got {matrix.shape}")
    coordinates, ratios = project_matrix(matrix)
    top_ids = trace["outputs"][0]["retrieved_ids"]
    spec = importlib.util.spec_from_file_location(
        "rag_visual_data", ROOT / "core/ai-mechanism/rag_visual_data.py")
    visual_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(visual_module)
    ranking, metric, direction = visual_module.ranking_from_trace(trace)
    visual_data = visual_module.prepare_rag_visual_data(trace)
    ranks = {item["source_id"]: item["rank"] for item in ranking}
    score_values = {item["source_id"]: item["value"] for item in ranking}
    duration = float(os.environ.get("V10_THREE_DURATION", "8"))
    vector_label = visual_data["vector_label"]
    output = {
        "schema": "ai-embedding-display-projection/v1",
        "source_trace_sha256": hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest(),
        "method": f"PCA by deterministic NumPy SVD over {len(vectors)} recorded vectors and the query vector",
        "source_dimension": int(matrix.shape[1]),
        "display_dimension": 3,
        "vector_label": vector_label,
        "explained_variance_ratio": ratios.tolist(),
        "projection_is_lossy": True,
        "geometry_semantics": f"display coordinates only; retrieval rankings and scores remain from original {matrix.shape[1]}D vectors",
        "trace_id": trace["trace_id"],
        "query_id": query["id"],
        "retrieval": {"metric": metric, "direction": direction,
                      "top_k_ids": top_ids, "top_k": len(top_ids),
                      "ranking": [{"id": item["source_id"], "rank": item["rank"],
                                   "score": item["value"]}
                                  for item in ranking],
                      "scores_and_ranks_source": "ai_trace.json"},
        "points": [{"id": item_id, "xyz": coordinates[i].tolist(),
                    "rank": ranks.get(item_id),
                    "score": score_values.get(item_id),
                    "kind": "query" if item_id == query["id"] else "chunk"}
                   for i, item_id in enumerate(ids)],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(vectors)} vectors + query projected from {matrix.shape[1]}D to 3D; "
          f"PCA variance {ratios.sum():.4f}; top-k={','.join(top_ids)}; duration={duration:g}s")
    print(OUT)


if __name__ == "__main__":
    main()
