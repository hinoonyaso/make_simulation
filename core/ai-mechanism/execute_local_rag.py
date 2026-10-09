"""A dependency-free, explicitly lexical RAG execution used for new local inputs.

This runner performs chunking, TF-IDF feature creation, cosine retrieval and context
assembly. It does not call a semantic embedding model or generate an LLM answer.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import re
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from primitives import chunk_windows


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w가-힣]+", text.casefold(), flags=re.UNICODE)


def execute_lexical_rag(document: str, question: str, *, chunk_size: int = 500,
                        overlap: int = 60, top_k: int = 3) -> dict[str, Any]:
    if not document.strip() or not question.strip():
        raise ValueError("document and question must be non-empty")
    if top_k < 1:
        raise ValueError("top_k must be positive")
    windows = chunk_windows(document, chunk_size, overlap)
    if not windows:
        raise ValueError("document produced no chunks")
    chunks = [{"id": f"chunk-{index+1:03d}", **window} for index, window in enumerate(windows)]
    tokenized = [_tokens(chunk["text"]) for chunk in chunks]
    query_tokens = _tokens(question)
    vocabulary = sorted(set(query_tokens).union(*(set(tokens) for tokens in tokenized)))
    if not vocabulary:
        raise ValueError("document and question contain no searchable tokens")
    index = {token: i for i, token in enumerate(vocabulary)}
    document_frequency = Counter(token for tokens in tokenized for token in set(tokens))

    def vector(tokens: list[str]) -> list[float]:
        term_counts = Counter(tokens)
        values = [0.0] * len(vocabulary)
        for token, count in term_counts.items():
            tf = count / max(len(tokens), 1)
            idf = math.log((1 + len(chunks)) / (1 + document_frequency[token])) + 1.0
            values[index[token]] = tf * idf
        norm = math.sqrt(sum(value * value for value in values))
        return [value / norm for value in values] if norm else values

    vectors = [vector(tokens) for tokens in tokenized]
    query_vector = vector(query_tokens)
    started = __import__("time").perf_counter()
    scored = []
    for chunk, values in zip(chunks, vectors):
        cosine = sum(a*b for a, b in zip(query_vector, values))
        scored.append({"source_id": chunk["id"], "value": cosine})
    # Score tie-breaking is deterministic by source ID; elapsed time reports the actual loop.
    scored.sort(key=lambda item: (-item["value"], item["source_id"]))
    elapsed = __import__("time").perf_counter() - started
    for rank, item in enumerate(scored, 1):
        item["rank"] = rank
    selected = scored[:min(top_k, len(scored))]
    source_hash = hashlib.sha256(document.encode("utf-8")).hexdigest()
    trace_id = f"rag-lexical:{source_hash[:12]}:{hashlib.sha256(question.encode()).hexdigest()[:8]}"
    values: list[dict[str, Any]] = []
    for chunk, features in zip(chunks, vectors):
        values.append({"id": chunk["id"], "kind": "text_chunk", "value": chunk["text"],
                       "char_start": chunk["start"], "char_end": chunk["end"],
                       "source_id": "document:source"})
        values.append({"id": f"vector:{chunk['id']}", "kind": "feature_vector",
                       "shape": [len(features)], "value": features,
                       "source_id": chunk["id"]})
    values.extend({"id": f"score:{item['source_id']}", "kind": "retrieval_score",
                   "score_type": "cosine_similarity", **item} for item in scored)
    context_text = "\n\n".join(next(c["text"] for c in chunks if c["id"] == item["source_id"])
                                for item in selected)
    transitions = [
        {"id": "document.to_chunks", "operation_id": "document.split",
         "before": "document:source", "after": [item["id"] for item in chunks],
         "summary": f"{len(document)} characters divided into {len(chunks)} overlapping windows"},
        {"id": "query.to_ranked_chunks", "operation_id": "retrieval.search",
         "before": "query:Q0", "after": [item["source_id"] for item in scored],
         "summary": "TF-IDF lexical cosine scores sorted descending"},
        {"id": "chunks.to_context", "operation_id": "context.assemble",
         "before": [item["source_id"] for item in selected], "after": "context:Q0",
         "summary": "selected source text joined in retrieval rank order"},
    ]
    return {
        "schema": "ai-mechanism-trace/v1", "trace_id": trace_id,
        "system": {"family": "RAG", "question": question,
                   "execution": "local lexical TF-IDF retrieval; no generative model",
                   "vector_representation": "lexical TF-IDF feature vectors; not semantic embeddings"},
        "inputs": [{"id": "document:source", "kind": "document", "text": document,
                    "sha256": source_hash},
                   {"id": "query:Q0", "kind": "query", "text": question,
                    "features": query_vector}],
        "operations": [
            {"id": "document.split", "kind": "operation", "label": "character-window chunking",
             "input_ids": ["document:source"], "output_ids": [c["id"] for c in chunks],
             "parameters": {"size": chunk_size, "overlap": overlap},
             "evidence": "model_execution", "execution_time_seconds": None},
            {"id": "embedding.encode", "kind": "operation", "label": "TF-IDF lexical features",
             "input_ids": [c["id"] for c in chunks],
             "output_ids": [f"vector:{c['id']}" for c in chunks],
             "parameters": {"vocabulary_size": len(vocabulary), "semantic": False},
             "evidence": "model_execution", "execution_time_seconds": None},
            {"id": "retrieval.search", "kind": "operation", "label": "cosine similarity",
             "input_ids": ["query:Q0", *[f"vector:{c['id']}" for c in chunks]],
             "output_ids": [item["source_id"] for item in selected],
             "parameters": {"metric": "cosine_similarity", "top_k": len(selected)},
             "evidence": "model_execution", "execution_time_seconds": elapsed},
            {"id": "context.assemble", "kind": "operation", "label": "ranked text join",
             "input_ids": [item["source_id"] for item in selected],
             "output_ids": ["context:Q0"], "evidence": "model_execution",
             "execution_time_seconds": None},
        ],
        "transitions": transitions, "intermediate_values": values,
        "outputs": [{"id": "context:Q0", "kind": "context", "text": context_text,
                     "retrieved_ids": [item["source_id"] for item in selected]}],
        "retrieval": {"metric": "TF-IDF cosine similarity", "direction": "descending",
                      "top_k": len(selected), "top_k_ids": [item["source_id"] for item in selected]},
        "provenance": {"runtime": "Python standard library", "retrieval_runtime_seconds": elapsed,
                       "model_execution": "lexical TF-IDF; no semantic embedding model and no LLM"},
        "visualization": {"projection": {"method": "computed from recorded lexical features"},
                          "coordinates": [], "projection_is_lossy": True,
                          "render_time_semantics": "presentation time; not inference latency",
                          "order": ["document.split", "embedding.encode", "retrieval.search",
                                    "context.assemble"]},
    }


def execute_files(document_path: str | Path, question: str, output_path: str | Path,
                  *, chunk_size: int = 500, overlap: int = 60, top_k: int = 3) -> dict[str, Any]:
    document_path = Path(document_path)
    document = document_path.read_text(encoding="utf-8")
    trace = execute_lexical_rag(document, question, chunk_size=chunk_size,
                                overlap=overlap, top_k=top_k)
    trace["provenance"]["source_document"] = str(document_path.resolve())
    trace["provenance"]["source_document_sha256"] = trace["inputs"][0]["sha256"]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return trace
