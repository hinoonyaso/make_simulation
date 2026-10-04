from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".codex" / "config.toml"


DOC_PATH = re.compile(r"`((?:core|optional|scripts|templates|references)/[\w./-]+\.(?:py|md|json|yaml|toml))")


def check_wiring() -> list[str]:
    """Catch docs that name files which no longer exist (the V9.0 drift)."""
    errors: list[str] = []
    manifest = json.loads((ROOT / "BUNDLE_MANIFEST.json").read_text(encoding="utf-8"))
    errors.extend(f"BUNDLE_MANIFEST deterministic entry missing: {p}"
                  for p in manifest.get("deterministic", []) if not (ROOT / p).exists())
    docs = [ROOT / "ROUTING.md", ROOT / "AGENTS.md", *ROOT.glob("core/*/SKILL.md"), *ROOT.glob("optional/*/SKILL.md")]
    for doc in docs:
        for ref in DOC_PATH.findall(doc.read_text(encoding="utf-8")):
            # Skill-local paths resolve from the skill directory, bundle paths from ROOT.
            if not ((doc.parent / ref).exists() or (ROOT / ref).exists()):
                errors.append(f"{doc.relative_to(ROOT)} references missing {ref}")
    links = ROOT / ".claude" / "skills"
    if links.exists():
        for link in links.iterdir():
            if not (link / "SKILL.md").exists():
                errors.append(f"broken Claude Code skill link: {link.relative_to(ROOT)}")
    return errors


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

        for ref in re.findall(r"(?:core|optional)/[\w./-]+?/SKILL\.md", child.get("developer_instructions", "")):
            if not (ROOT / ref).exists():
                errors.append(f"{name}: developer_instructions points to missing {ref}")

    required = [ROOT / "AGENTS.md", ROOT / "ROUTING.md", ROOT / "MODEL_ROUTING.yaml"]
    errors.extend(f"missing required file: {p}" for p in required if not p.exists())
    errors.extend(check_wiring())

    if errors:
        print("FAIL")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    print(f"PASS: {checked} Codex agent configs validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
