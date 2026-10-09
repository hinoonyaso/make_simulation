"""Dataset-independent preparation for the trace-driven RAG Manim/Three.js views."""
from __future__ import annotations

import math
from typing import Any


def ranking_from_trace(trace: dict[str, Any]) -> tuple[list[dict[str, Any]], str, str]:
    """Return recorded ranking rows, metric label and sort direction."""
    values = trace.get("intermediate_values", [])
    generic = [item for item in values if item.get("kind") == "retrieval_score"]
    if generic:
        retrieval = trace.get("retrieval", {})
        return (sorted(generic, key=lambda item: item["rank"]),
                str(retrieval.get("metric", "recorded score")),
                str(retrieval.get("direction", "ascending")))
    distances = [item for item in values if item.get("kind") == "squared_l2_distance"]
    if distances:
        return sorted(distances, key=lambda item: item["rank"]), "squared L2", "ascending"
    raise ValueError("trace has no supported recorded retrieval scores")


def chunk_overlap_pairs(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return every positive source-character intersection without assuming IDs/order."""
    ordered = sorted(chunks, key=lambda item: (item.get("char_start", 0), item.get("char_end", 0)))
    active: list[dict[str, Any]] = []
    overlaps = []
    for current in ordered:
        if "char_start" not in current or "char_end" not in current:
            continue
        active = [item for item in active if item["char_end"] > current["char_start"]]
        for prior in active:
            start = max(prior["char_start"], current["char_start"])
            end = min(prior["char_end"], current["char_end"])
            if end > start:
                overlaps.append({"left_id": prior["id"], "right_id": current["id"],
                                 "char_start": start, "char_end": end, "length": end-start})
        active.append(current)
    return overlaps


def prepare_rag_visual_data(trace: dict[str, Any]) -> dict[str, Any]:
    inputs = trace.get("inputs", [])
    source = next((item for item in inputs if item.get("kind") == "document"), None)
    query = next((item for item in inputs if item.get("kind") == "query"), None)
    if not query:
        raise ValueError("trace must contain a query input")
    chunks = [item for item in trace.get("intermediate_values", [])
              if item.get("kind") == "text_chunk"]
    if not chunks:
        raise ValueError("trace must contain text_chunk values")
    ranking, metric, direction = ranking_from_trace(trace)
    rank_by_source = {item.get("source_id"): item for item in ranking}
    top_ids = next((item.get("retrieved_ids", []) for item in trace.get("outputs", [])
                    if isinstance(item, dict)), [])
    top_k = trace.get("retrieval", {}).get("top_k", len(top_ids))
    vectors = [item for item in trace.get("intermediate_values", [])
               if item.get("kind") in {"embedding", "feature_vector"}]
    vector_ids = {item["id"].removeprefix("vector:"): item["value"] for item in vectors
                  if isinstance(item.get("value"), list)}
    query_vector = query.get("embedding", query.get("features"))

    coords = {item["id"]: item.get("xy", item.get("xyz", [])[:2])
              for item in trace.get("visualization", {}).get("coordinates", [])
              if isinstance(item, dict) and isinstance(item.get("id"), str)}
    if query["id"] not in coords or any(chunk["id"] not in coords for chunk in chunks):
        if not vectors or not isinstance(query_vector, list):
            # Score-only traces remain useful for ranking and context; arrange candidates by rank.
            coords = {item["source_id"]: [index, 0]
                      for index, item in enumerate(ranking) if item.get("source_id")}
            coords[query["id"]] = [-1, 0]
        else:
            try:
                import numpy as np
            except ImportError as exc:
                raise ValueError("NumPy is required to project the recorded vectors for display") from exc
            matrix = np.asarray([vector_ids[chunk["id"]] for chunk in chunks] + [query_vector], dtype=float)
            if matrix.ndim != 2 or not np.isfinite(matrix).all():
                raise ValueError("recorded vectors must have a finite, consistent shape")
            centered = matrix - matrix.mean(axis=0)
            if matrix.shape[1] == 1:
                xy = np.column_stack((centered[:, 0], np.zeros(len(centered))))
            else:
                _, _, vt = np.linalg.svd(centered, full_matrices=False)
                xy = centered @ vt[:min(2, len(vt))].T
                if xy.shape[1] == 1:
                    xy = np.column_stack((xy[:, 0], np.zeros(len(xy))))
            scale = max(float(np.abs(xy).max()), 1e-9)
            xy = xy / scale
            coords = {chunk["id"]: xy[index].tolist() for index, chunk in enumerate(chunks)}
            coords[query["id"]] = xy[-1].tolist()
    for chunk in chunks:
        coords.setdefault(chunk["id"], [0.0, 0.0])
    coords.setdefault(query["id"], [0.0, 0.0])

    source_text = source.get("text", "") if source else ""
    overlaps = chunk_overlap_pairs(chunks)
    representative_overlap = max(overlaps, key=lambda item: item["length"], default=None)
    raw_vector_label = trace.get("system", {}).get("vector_representation", "recorded vectors")
    dimensions = len(query_vector) if isinstance(query_vector, list) else None
    if str(raw_vector_label).startswith("lexical TF-IDF"):
        vector_label = "단어 TF-IDF 특징 벡터 · 의미 임베딩 아님"
    elif dimensions:
        vector_label = f"저장된 {dimensions}차원 벡터 임베딩"
    else:
        vector_label = str(raw_vector_label)[:48]
    return {
        "trace_id": trace.get("trace_id", "unknown"), "source": source,
        "source_text": source_text, "source_length": len(source_text), "chunks": chunks,
        "query": query, "ranking": ranking, "rank_by_source": rank_by_source,
        "top_ids": top_ids, "top_k": top_k, "metric": metric, "direction": direction,
        "coords": coords, "vector_count": len(vectors),
        "vector_label": vector_label,
        "overlaps": overlaps, "representative_overlap": representative_overlap,
        "outputs": trace.get("outputs", []),
    }
