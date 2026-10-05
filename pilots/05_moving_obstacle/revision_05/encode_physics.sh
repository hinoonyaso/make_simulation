#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ffmpeg -hide_banner -loglevel error -y -framerate 30 -i output/blender/frames/frame_%04d.png -c:v libx264 -threads 2 -preset fast -crf 17 -pix_fmt yuv420p -r 30 output/blender/physics_raw.mp4
