from __future__ import annotations
import json, math, sys
from pathlib import Path

# Manim and Blender both read this file, so units and per-sample shape must be explicit.
SCHEMA_PREFIX='robotics-visual-trace/'

def _numeric(v):
    if isinstance(v,bool): return False
    if isinstance(v,(int,float)): return True
    return isinstance(v,list) and bool(v) and all(_numeric(x) for x in v)

def _finite(v):
    if isinstance(v,list): return all(_finite(x) for x in v)
    return math.isfinite(v)

def validate(path):
    try: d=json.loads(Path(path).read_text(encoding='utf-8'))
    except FileNotFoundError: return [f'missing trace file: {path}']
    except json.JSONDecodeError as exc: return [f'invalid JSON: {exc}']
    e=[]
    if not str(d.get('schema','')).startswith(SCHEMA_PREFIX): e.append(f'schema must start with {SCHEMA_PREFIX!r}')
    units=d.get('units')
    if not isinstance(units,dict) or 'time' not in units: e.append('units{} must declare at least "time"'); units=units if isinstance(units,dict) else {}
    samples=d.get('samples')
    if not isinstance(samples,list) or not samples: return e+['samples[] missing/empty']
    keys=None; last=None
    first=samples[0] if isinstance(samples[0],dict) else {}
    numeric_keys={k for k,v in first.items() if k!='t' and _numeric(v)}
    for i,s in enumerate(samples):
        if not isinstance(s,dict): e.append(f'samples[{i}]: not an object'); continue
        if keys is None: keys=set(s)
        elif set(s)!=keys: e.append(f'samples[{i}]: keys {sorted(set(s))} differ from samples[0] {sorted(keys)}')
        if 't' not in s: e.append(f'samples[{i}]: missing t'); continue
        try: t=float(s['t'])
        except Exception: e.append(f'samples[{i}]: invalid t'); continue
        if last is not None and t < last: e.append(f'samples[{i}]: time decreases')
        last=t
        for k,v in s.items():
            if k in numeric_keys and not _numeric(v): e.append(f'samples[{i}].{k}: expected numeric like samples[0]')
            if k=='t' or not _numeric(v): continue
            if not _finite(v): e.append(f'samples[{i}].{k}: non-finite value')
            if i==0 and k not in units: e.append(f'units missing numeric field "{k}" (use "1" if dimensionless)')
    return e

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: validate_trace.py trace.json')
    errs=validate(sys.argv[1])
    if errs:
        print('FAIL'); print('\n'.join('- '+x for x in errs)); raise SystemExit(1)
    print('PASS')
