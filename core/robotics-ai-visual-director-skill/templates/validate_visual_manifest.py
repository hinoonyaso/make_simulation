from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

ALLOWED_TOOLS={"M","B","E"}
ALLOWED_EVIDENCE={"illustration","toy_simulation","trace_playback","model_execution","reported_result"}
# Evidence modes that claim real computed values must point at the shared trace.
TRACE_REQUIRED={"trace_playback","model_execution"}
BUNDLE=Path(__file__).resolve().parents[3]

def _trace_validator():
    spec=importlib.util.spec_from_file_location("validate_trace",BUNDLE/"core/shared-data/validate_trace.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.validate

def validate(path: str, require_media: bool=False):
    manifest=Path(path).resolve(); base=manifest.parent
    data=json.loads(manifest.read_text(encoding="utf-8"))
    beats=data.get("beats") or []
    long_form=data.get("format") == "long_form"
    max_beat_sec=60 if long_form else 20
    max_beats=48 if long_form else 16
    errors=[]; warnings=[]; checked_traces={}
    if not beats: errors.append("beats is empty")
    ids=set()
    for i,b in enumerate(beats):
        tag=f"beats[{i}]"
        bid=b.get("id")
        if not bid: errors.append(f"{tag}: missing id")
        elif bid in ids: errors.append(f"{tag}: duplicate id {bid}")
        ids.add(bid)
        if not str(b.get("text","")).strip(): errors.append(f"{tag}: missing narration text")
        try:
            sec=float(b.get("sec",0))
            if not 0.4 <= sec <= max_beat_sec: errors.append(f"{tag}: sec must be 0.4..{max_beat_sec}")
        except Exception: errors.append(f"{tag}: invalid sec")
        if not str(b.get("object","")).strip(): errors.append(f"{tag}: missing persistent object")
        if not str(b.get("state_change","")).strip(): errors.append(f"{tag}: missing state_change")
        if not str(b.get("focus","")).strip(): errors.append(f"{tag}: missing focus")
        if b.get("tool") not in ALLOWED_TOOLS: errors.append(f"{tag}: tool must be M/B/E")
        evidence=b.get("evidence")
        if evidence not in ALLOWED_EVIDENCE: errors.append(f"{tag}: invalid evidence")
        trace=str(b.get("trace","")).strip()
        if evidence in TRACE_REQUIRED and not trace: errors.append(f"{tag}: evidence={evidence} requires a shared trace path")
        elif evidence=="toy_simulation" and not trace: warnings.append(f"{tag}: toy_simulation without trace; renderers may invent values")
        if trace:
            tp=(base/trace).resolve()
            if tp not in checked_traces: checked_traces[tp]=_trace_validator()(str(tp))
            errors.extend(f"{tag}: trace {trace}: {e}" for e in checked_traces[tp])
        for field in ("audio","media"):
            value=str(b.get(field,"")).strip()
            if value and not (base/value).exists(): errors.append(f"{tag}: {field} not found: {value}")
        for field in ("min_sec","media_in","media_out"):
            if b.get(field) is not None:
                try: float(b[field])
                except Exception: errors.append(f"{tag}: {field} must be seconds")
        if b.get("media_in") is not None and b.get("media_out") is not None:
            try:
                if float(b["media_out"])<=float(b["media_in"]): errors.append(f"{tag}: media_out must be > media_in")
            except Exception: pass
        if require_media and b.get("tool") in {"M","B"} and not str(b.get("media","")).strip():
            errors.append(f"{tag}: tool={b.get('tool')} beat has no rendered media path")
    if len(beats)>max_beats: errors.append(f"too many beats for this format (maximum {max_beats}); merge non-essential beats")
    return errors, warnings

if __name__=="__main__":
    args=[a for a in sys.argv[1:] if a!="--require-media"]
    if len(args)!=1: raise SystemExit("usage: validate_visual_manifest.py visual_manifest.json [--require-media]")
    errors,warnings=validate(args[0],"--require-media" in sys.argv)
    for w in warnings: print(f"WARN {w}")
    if errors:
        print("FAIL")
        print("\n".join(f"- {e}" for e in errors))
        raise SystemExit(1)
    print("PASS")
