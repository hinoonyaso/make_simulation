#!/usr/bin/env python3
"""Validate the checked-in AI trace or adapt an explicitly supplied RAG run."""
import argparse
import json
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
default_trace = ROOT / "pilots/v10_rag_poc/data/ai_trace.json"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-run", type=Path,
                    help="optional naive-rag-run/v1 file; when omitted validate the checked-in trace")
parser.add_argument("--trace", type=Path, default=default_trace,
                    help=f"AI trace to validate or write (default: {default_trace.relative_to(ROOT)})")
args = parser.parse_args()

if args.source_run:
    trace = module.adapt_rag_run(args.source_run, args.trace)
    print(f"Wrote {args.trace} ({len(trace['operations'])} operations)")
else:
    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    errors = module.validate_trace(trace)
    if errors:
        raise SystemExit("FAIL\n" + "\n".join(f"- {error}" for error in errors))
    print(f"PASS {trace['schema']}: {len(trace['operations'])} operations, "
          f"{len(trace['intermediate_values'])} values; checked-in trace reused, no source run needed")
