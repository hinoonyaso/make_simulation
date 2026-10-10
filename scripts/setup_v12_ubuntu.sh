#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:---check}"
if [[ "$MODE" != "--check" && "$MODE" != "--install" ]]; then
  echo "usage: $0 [--check|--install]" >&2
  exit 2
fi

packages=(build-essential pkg-config python3-dev python3-venv python3-tk ffmpeg
  libcairo2-dev libpango1.0-dev fonts-nanum iproute2 can-utils kmod)
missing=()
for package in "${packages[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    missing+=("$package")
  fi
done

if [[ "$MODE" == "--check" ]]; then
  if ((${#missing[@]})); then
    printf 'OPTIONAL_MISSING system packages: %s\n' "${missing[*]}"
  else
    echo "READY system package prerequisites"
  fi
  (cd "$ROOT_DIR" && uv run python scripts/inspect_engineering_env.py --check all)
  exit $?
fi

if ((${#missing[@]})); then
  if [[ "$(id -u)" -eq 0 ]]; then
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing[@]}"
  elif command -v sudo >/dev/null && sudo -n true 2>/dev/null; then
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing[@]}"
  else
    printf 'BLOCKED: administrator permission required. Run: sudo apt install -y %s\n' "${missing[*]}" >&2
    exit 3
  fi
fi

cd "$ROOT_DIR"
uv sync --group sim-math --group sim-can --group sim-motor
uv run python -c 'import sympy, scipy, control, can, cantools, motulator; print("V12 ENGINEERING IMPORT PASS")'
uv run python scripts/inspect_engineering_env.py --check all

history="$ROOT_DIR/output/v12_setup_history.jsonl"
mkdir -p "$(dirname "$history")"
python3 - "$history" <<'PY'
import json, platform, sys, time
from pathlib import Path
target = Path(sys.argv[1])
record = {"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "action": "install", "platform": platform.platform(), "python": platform.python_version()}
with target.open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(record, sort_keys=True) + "\n")
PY
echo "V12 environment setup complete"
