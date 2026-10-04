from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".codex" / "config.toml"


def main() -> int:
    data = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    agents = data.get("agents", {})
    errors: list[str] = []
    checked = 0
    for name, spec in agents.items():
        if not isinstance(spec, dict) or "config_file" not in spec:
            continue
        path = CONFIG.parent / spec["config_file"]
        if not path.exists():
            errors.append(f"missing agent config: {name}: {path}")
            continue
        try:
            child = tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid TOML: {name}: {exc}")
            continue
        if not child.get("model"):
            errors.append(f"missing model: {name}")
        if not child.get("model_reasoning_effort"):
            errors.append(f"missing effort: {name}")
        checked += 1

    required = [ROOT / "AGENTS.md", ROOT / "ROUTING.md", ROOT / "MODEL_ROUTING.yaml"]
    errors.extend(f"missing required file: {p}" for p in required if not p.exists())

    if errors:
        print("FAIL")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    print(f"PASS: {checked} Codex agent configs validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
