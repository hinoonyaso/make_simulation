"""Adapter from the local Naive RAG execution record to ai-mechanism-trace/v1.

The adapter preserves source computation and labels display projections as lossy.
It never recomputes a score or presents presentation timestamps as model latency.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCHEMA = "ai-mechanism-trace/v1"


def adapt_rag_run(run_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    source_path = Path(run_path).resolve()
    run_data = json.loads(source_path.read_text(encoding="utf-8"))
    if run_data.get("schema") != "naive-rag-run/v1":
        raise ValueError("expected naive-rag-run/v1")
    runs = run_data.get("runs") or []
    if not runs:
        raise ValueError("RAG run has no recorded query")
    selected = runs[0]
    chunks = run_data.get("chunks") or []
    by_id = {chunk["id"]: chunk for chunk in chunks}

    operations = [
        {"id": "document.load", "kind": "input", "label": "load source document",
         "input_ids": [run_data["source_sha256"]], "output_ids": ["document:source"],
         "evidence": "model_execution", "execution_time_seconds": None},
        {"id": "document.split", "kind": "operation", "label": "RecursiveCharacterTextSplitter",
         "input_ids": ["document:source"], "output_ids": [c["id"] for c in chunks],
         "parameters": dict(run_data["splitter"]), "evidence": "model_execution",
         "execution_time_seconds": None},
        {"id": "embedding.encode", "kind": "operation", "label": run_data["embedding"]["model"],
         "input_ids": [c["id"] for c in chunks], "output_ids": [f"vector:{c['id']}" for c in chunks],
         "parameters": dict(run_data["embedding"]), "evidence": "model_execution",
         "execution_time_seconds": None},
        {"id": "retrieval.search", "kind": "operation", "label": run_data["index"]["class"],
         "input_ids": ["query:Q0", *[f"vector:{c['id']}" for c in chunks]],
         "output_ids": [r["chunk_id"] for r in selected["ranking"][:3]],
         "parameters": dict(run_data["index"]), "evidence": "model_execution",
         "execution_time_seconds": None},
        {"id": "context.assemble", "kind": "operation", "label": "format_docs",
         "input_ids": [r["chunk_id"] for r in selected["ranking"][:3]],
         "output_ids": ["context:Q0"], "evidence": "model_execution",
         "execution_time_seconds": None},
        {"id": "answer.generate", "kind": "output", "label": run_data["llm"]["model"],
         "input_ids": ["context:Q0", "query:Q0"], "output_ids": ["answer:Q0"],
         "evidence": "model_execution",
         "execution_time_seconds": selected.get("generation_seconds")},
    ]
    transitions = [
        {"id": "document.to_chunks", "operation_id": "document.split",
         "before": "document:source", "after": [c["id"] for c in chunks],
         "summary": f"{len(run_data['source_text'])} characters split into {len(chunks)} stored chunks"},
        {"id": "query.to_ranked_chunks", "operation_id": "retrieval.search",
         "before": "query:Q0", "after": [r["chunk_id"] for r in selected["ranking"][:3]],
         "summary": "full 384-dimensional squared-L2 ranking; lower is nearer"},
        {"id": "chunks.to_context", "operation_id": "context.assemble",
         "before": [r["chunk_id"] for r in selected["ranking"][:3]], "after": "context:Q0",
         "summary": "ranked source text joined with the recorded separator"},
    ]
    values = []
    for chunk in chunks:
        values.append({"id": chunk["id"], "kind": "text_chunk", "value": chunk["text"],
                       "char_start": chunk["start"], "char_end": chunk["end"],
                       "source_id": "document:source"})
        values.append({"id": f"vector:{chunk['id']}", "kind": "embedding",
                       "shape": [run_data["embedding"]["dimension"]], "value": chunk["vector"],
                       "source_id": chunk["id"]})
    for rank, item in enumerate(selected["ranking"], start=1):
        values.append({"id": f"distance:{item['chunk_id']}", "kind": "squared_l2_distance",
                       "value": item["squared_l2"], "rank": rank, "source_id": item["chunk_id"]})
    values.append({"id": "context:Q0", "kind": "text", "value": selected["context"],
                   "source_chunk_ids": [r["chunk_id"] for r in selected["ranking"][:3]]})
    trace = {
        "schema": SCHEMA,
        "trace_id": f"rag:{run_data['source_sha256'][:12]}:Q0",
        "system": {"family": "RAG", "question": selected["question"],
                   "execution": "recorded local model execution"},
        "inputs": [{"id": "document:source", "kind": "document",
                    "text": run_data["source_text"], "sha256": run_data["source_sha256"]},
                   {"id": "query:Q0", "kind": "query", "text": selected["question"],
                    "embedding": selected["query_vector"]}],
        "operations": operations,
        "transitions": transitions,
        "intermediate_values": values,
        "outputs": [{"id": "answer:Q0", "kind": "answer",
                     "text": selected.get("answer", ""),
                     "retrieved_ids": [r["chunk_id"] for r in selected["ranking"][:3]]}],
        "provenance": {"source_run": str(source_path),
                       "source_run_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                       "source_data_sha256": run_data["source_sha256"],
                       "embedding_model": run_data["embedding"]["model"],
                       "generation_model": run_data["llm"]["model"],
                       "retrieval": dict(run_data["index"]),
                       "retrieval_runtime_seconds": None,
                       "timing_note": "Only answer generation was timed in the source run; other operation times are null."},
        "visualization": {"projection": run_data.get("projection", {}),
                          "coordinates": [{"id": c["id"], "xy": c["projection"]}
                                          for c in chunks] +
                                         [{"id": "query:Q0", "xy": selected["projection"]}],
                          "projection_is_lossy": True,
                          "render_time_semantics": "presentation time; not inference latency",
                          "order": ["document.split", "embedding.encode", "retrieval.search",
                                    "context.assemble", "answer.generate"]},
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    errors = validate_trace(trace)
    if errors:
        Path(output_path).unlink(missing_ok=True)
        raise ValueError("generated invalid AI trace: " + "; ".join(errors))
    return trace


def validate_trace(trace: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(trace, dict):
        return ["trace root must be an object"]
    if trace.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    for field in ("inputs", "operations", "transitions", "intermediate_values", "outputs"):
        if not isinstance(trace.get(field), list) or not trace[field]:
            errors.append(f"{field} must be a non-empty list")
    # Stop structural walking when one of the core collections has the wrong type.
    if any(not isinstance(trace.get(field), list) for field in
           ("inputs", "operations", "transitions", "intermediate_values", "outputs")):
        return errors
    ids: set[str] = set()
    for group in ("inputs", "operations", "intermediate_values", "outputs"):
        for item in trace.get(group, []):
            if not isinstance(item, dict):
                errors.append(f"{group} item must be an object")
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                errors.append(f"{group} item missing id")
            elif item_id in ids:
                errors.append(f"duplicate data id: {item_id}")
            else:
                ids.add(item_id)
    op_ids = {o.get("id") for o in trace.get("operations", []) if isinstance(o, dict)}
    for tr in trace.get("transitions", []):
        if not isinstance(tr, dict):
            errors.append("transitions item must be an object")
            continue
        if tr.get("operation_id") not in op_ids:
            errors.append(f"transition {tr.get('id')} references unknown operation")
    for op in trace.get("operations", []):
        if not isinstance(op, dict):
            continue
        if op.get("evidence") not in {"model_execution", "reported_result", "toy_simulation", "illustration"}:
            errors.append(f"operation {op.get('id')} has invalid evidence")
        elapsed = op.get("execution_time_seconds")
        if elapsed is not None and (not isinstance(elapsed, (int, float)) or
                                    not math.isfinite(elapsed) or elapsed < 0):
            errors.append(f"operation {op.get('id')} execution_time_seconds must be null or nonnegative finite seconds")
    values = {v.get("id"): v for v in trace.get("intermediate_values", [])
              if isinstance(v, dict)}
    for item in values.values():
        if item.get("kind") in {"embedding", "feature_vector"}:
            vec = item.get("value")
            if not isinstance(vec, list) or item.get("shape") != [len(vec)] or not vec:
                errors.append(f"embedding {item.get('id')} shape mismatch")
            elif not all(isinstance(x, (int, float)) and math.isfinite(x) for x in vec):
                errors.append(f"embedding {item.get('id')} has non-finite values")
        if item.get("kind") == "squared_l2_distance":
            value = item.get("value")
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                errors.append(f"distance {item.get('id')} must be finite and nonnegative")
    for item in trace.get("inputs", []):
        if not isinstance(item, dict):
            continue
        vector = item.get("embedding")
        if vector is not None and (not isinstance(vector, list) or not vector or
                                   not all(isinstance(x, (int, float)) and math.isfinite(x) for x in vector)):
            errors.append(f"input {item.get('id')} has invalid embedding")
    dimensions = {len(item["value"]) for item in values.values()
                  if item.get("kind") in {"embedding", "feature_vector"}
                  and isinstance(item.get("value"), list)}
    query_dimensions = {len(item[key]) for item in trace.get("inputs", []) if isinstance(item, dict)
                        for key in ("embedding", "features") if isinstance(item.get(key), list)}
    if len(dimensions) > 1 or (dimensions and query_dimensions and dimensions != query_dimensions):
        errors.append("query and document embedding dimensions must match")
    ranked = [v for v in values.values() if v.get("kind") == "squared_l2_distance"]
    if ranked:
        ranks = [v.get("rank") for v in ranked]
        if any(type(rank) is not int or rank < 1 for rank in ranks) or len(set(ranks)) != len(ranks):
            errors.append("retrieval ranks must be unique positive integers")
        ordered = sorted(ranked, key=lambda v: v.get("rank", 0))
        scores = [v["value"] for v in ordered]
        if scores != sorted(scores):
            errors.append("squared-L2 ranking must be ascending")
    generic_ranked = [v for v in values.values() if v.get("kind") == "retrieval_score"]
    if generic_ranked:
        ranks = [v.get("rank") for v in generic_ranked]
        if any(type(rank) is not int or rank < 1 for rank in ranks) or len(set(ranks)) != len(ranks):
            errors.append("retrieval ranks must be unique positive integers")
        retrieval = trace.get("retrieval", {})
        direction = retrieval.get("direction") if isinstance(retrieval, dict) else None
        ordered = sorted(generic_ranked, key=lambda v: v.get("rank", 0))
        scores = [v.get("value") for v in ordered]
        if not all(isinstance(score, (int, float)) and math.isfinite(score) for score in scores):
            errors.append("retrieval scores must be finite numbers")
        elif direction == "ascending" and scores != sorted(scores):
            errors.append("retrieval scores must be ascending")
        elif direction == "descending" and scores != sorted(scores, reverse=True):
            errors.append("retrieval scores must be descending")
        elif direction not in {"ascending", "descending"}:
            errors.append("retrieval direction must be ascending or descending")
    known_sources = {v.get("source_id") for v in values.values()}
    known_sources.update(item.get("id") for item in values.values())
    known_sources.update(item.get("id") for item in trace.get("inputs", []))
    for out in trace.get("outputs", []):
        if not isinstance(out, dict):
            continue
        for source_id in out.get("retrieved_ids", []):
            if source_id not in known_sources:
                errors.append(f"output references unknown retrieved source {source_id}")
    provenance = trace.get("provenance", {})
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
        provenance = {}
    retrieval_meta = trace.get("retrieval", {})
    if not isinstance(retrieval_meta, dict):
        errors.append("retrieval must be an object")
        retrieval_meta = {}
    if provenance.get("retrieval_runtime_seconds") is not None:
        elapsed = provenance["retrieval_runtime_seconds"]
        if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
            errors.append("retrieval_runtime_seconds must be null or nonnegative finite seconds")
    visualization = trace.get("visualization", {})
    if not isinstance(visualization, dict):
        errors.append("visualization must be an object")
        visualization = {}
    if visualization.get("projection_is_lossy") is not True:
        errors.append("visualization must disclose lossy projection")
    if visualization.get("render_time_semantics") != "presentation time; not inference latency":
        errors.append("presentation time must be distinguished from inference latency")
    if generic_ranked and retrieval_meta.get("top_k") is not None:
        top_k = retrieval_meta["top_k"]
        if type(top_k) is not int or top_k < 1:
            errors.append("retrieval top_k must be a positive integer")
    return errors
