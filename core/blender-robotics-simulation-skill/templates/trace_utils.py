from __future__ import annotations
import json
from pathlib import Path

def load_trace(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('samples'), list):
        raise ValueError('trace must be an object containing samples[]')
    return data

def positions(trace, key='position'):
    return [s[key] for s in trace['samples'] if key in s]
