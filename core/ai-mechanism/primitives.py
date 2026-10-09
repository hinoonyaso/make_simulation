"""Small deterministic RAG state operations shared by renderers."""
from __future__ import annotations

from typing import Any


def chunk_windows(text: str, size: int, overlap: int) -> list[dict[str, Any]]:
    if not text:
        return []
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("require size > 0 and 0 <= overlap < size")
    step = size - overlap
    result = []
    for start in range(0, len(text), step):
        end = min(len(text), start + size)
        result.append({"start": start, "end": end, "text": text[start:end]})
        if end == len(text):
            break
    return result


def select_top_k(ranking: list[dict[str, Any]], k: int, score_key: str,
                 lower_is_better: bool = True) -> list[dict[str, Any]]:
    if k < 1:
        raise ValueError("k must be positive")
    for item in ranking:
        if score_key not in item:
            raise ValueError(f"missing score {score_key}")
    return sorted(ranking, key=lambda item: (item[score_key] if lower_is_better else -item[score_key],
                                             item.get("id", "")))[:k]


def assemble_context(chunks: list[dict[str, Any]], separator: str = "\n\n") -> dict[str, Any]:
    ids = [str(item["id"]) for item in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("context chunk IDs must be unique")
    return {"text": separator.join(item["text"] for item in chunks), "source_ids": ids}
