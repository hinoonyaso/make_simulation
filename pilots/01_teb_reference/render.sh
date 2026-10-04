#!/usr/bin/env bash
# Usage: ./render.sh S1 PREVIEW stills 1 120 240   |   ./render.sh S3 FINAL anim
set -euo pipefail
BLENDER='/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe'
SCRIPT=$(wslpath -w "$(dirname "$(readlink -f "$0")")/blender_shots.py")
"$BLENDER" --background --factory-startup --python-exit-code 1 --python "$SCRIPT" -- "$@"
