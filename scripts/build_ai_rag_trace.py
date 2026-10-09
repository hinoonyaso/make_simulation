#!/usr/bin/env python3
"""Project a saved RAG model execution into the independent AI trace schema."""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
out = ROOT / "pilots/v10_rag_poc/data/ai_trace.json"
trace = module.adapt_rag_run(ROOT / "pilots/07_naive_rag/data/rag_run.json", out)
print(f"Wrote {out.relative_to(ROOT)} ({len(trace['operations'])} operations)")
