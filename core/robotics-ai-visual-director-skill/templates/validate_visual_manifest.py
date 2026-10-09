from __future__ import annotations
import importlib.util, json, sys
from json import JSONDecodeError
from pathlib import Path

ALLOWED_TOOLS={"M","B","E"}
ALLOWED_EVIDENCE={"illustration","toy_simulation","trace_playback","model_execution","reported_result"}
# Evidence modes that claim real computed values must point at the shared trace.
TRACE_REQUIRED={"trace_playback","model_execution"}
BUNDLE=Path(__file__).resolve().parents[3]

def _trace_validator(trace_path):
    """Return a path validator that reports file/schema failures as errors."""
    path = Path(trace_path)

    def validate_trace_file(_path=None):
        target = Path(_path) if _path is not None else path
        try:
            raw = target.read_text(encoding="utf-8")
        except FileNotFoundError:
            return [f"missing trace file: {target}"]
        except PermissionError:
            return [f"unreadable trace file: {target}"]
        except OSError as exc:
            return [f"cannot read trace file {target}: {exc}"]
        except UnicodeDecodeError as exc:
            return [f"trace is not valid UTF-8: {exc}"]
        try:
            data = json.loads(raw)
        except JSONDecodeError as exc:
            return [f"invalid JSON: {exc}"]
        if not isinstance(data, dict):
            return ["trace root must be a JSON object"]
        schema = data.get("schema")
        if schema == "ai-mechanism-trace/v1":
            validator_path = BUNDLE / "core/ai-mechanism/rag_trace.py"
            module_name = "validate_ai_trace"
        elif schema == "mechanism-envelope/v1":
            validator_path = BUNDLE / "core/mechanism/trace_contract.py"
            module_name = "validate_mechanism_envelope"
        elif isinstance(schema, str) and schema.startswith("robotics-visual-trace/"):
            validator_path = BUNDLE / "core/shared-data/validate_trace.py"
            module_name = "validate_trace"
        else:
            return [f"unsupported trace schema: {schema!r}"]
        try:
            spec = importlib.util.spec_from_file_location(module_name, validator_path)
            if spec is None or spec.loader is None:
                return [f"could not load validator for schema {schema!r}"]
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if schema == "ai-mechanism-trace/v1":
                errors = module.validate_trace(data)
            elif schema == "mechanism-envelope/v1":
                errors = module.validate_envelope(data)
                # Dispatch known V11 topics through their domain validator so
                # mathematically inconsistent payloads cannot pass as schema-only traces.
                try:
                    if str(BUNDLE) not in sys.path:
                        sys.path.insert(0, str(BUNDLE))
                    from core.mechanism.registry import MechanismRegistry
                    capability = MechanismRegistry().resolve(data.get("topic", ""))
                    if capability is None:
                        errors.append(f"unknown mechanism topic for domain trace validation: {data.get('topic')!r}")
                    elif capability.get("trace_schema") != schema:
                        errors.append(f"mechanism topic {data.get('topic')!r} does not declare trace schema {schema!r}")
                    elif capability.get("implementation_status") == "ready":
                        adapter = MechanismRegistry().load_adapter(data["topic"])
                        errors.extend(adapter.validate(data))
                    else:
                        errors.append(f"mechanism topic {data.get('topic')!r} has no ready domain validator")
                except Exception as exc:
                    errors.append(f"domain trace validation failed safely: {type(exc).__name__}: {exc}")
            else:
                errors = module.validate(str(target))
            return list(errors)
        except Exception as exc:
            return [f"trace validation failed safely: {type(exc).__name__}: {exc}"]

    return validate_trace_file

def validate(path: str, require_media: bool=False):
    manifest=Path(path).resolve(); base=manifest.parent
    try:
        data=json.loads(manifest.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"missing manifest file: {manifest}"], []
    except PermissionError:
        return [f"unreadable manifest file: {manifest}"], []
    except OSError as exc:
        return [f"cannot read manifest file {manifest}: {exc}"], []
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"invalid manifest JSON: {exc}"], []
    if not isinstance(data, dict):
        return ["manifest root must be a JSON object"], []
    beats=data.get("beats") or []
    if not isinstance(beats, list):
        return ["beats must be a list"], []
    long_form=data.get("format") == "long_form"
    max_beat_sec=60 if long_form else 20
    max_beats=48 if long_form else 16
    errors=[]; warnings=[]; checked_traces={}
    if not beats: errors.append("beats is empty")
    ids=set()
    for i,b in enumerate(beats):
        tag=f"beats[{i}]"
        if not isinstance(b, dict):
            errors.append(f"{tag}: must be an object")
            continue
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
            if tp not in checked_traces: checked_traces[tp]=_trace_validator(tp)()
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
