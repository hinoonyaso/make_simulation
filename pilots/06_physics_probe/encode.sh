#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ffmpeg -hide_banner -loglevel error -y -framerate 30 -i output/frames/frame_%04d.png -vf "drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='동일한 바퀴 모터 명령 · 장애물 없음':x=80:y=65:fontsize=42:fontcolor=0x20242a:enable='lt(t,4)',drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='동일한 바퀴 모터 명령 · 드럼 있음':x=80:y=65:fontsize=42:fontcolor=0x20242a:enable='gte(t,4)',drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='교육용 단순 물리 모형 · 실제 Nav2 실행 아님 · 2배속':x=80:y=h-90:fontsize=32:fontcolor=0x20242a" -c:v libx264 -crf 18 -pix_fmt yuv420p -r 30 output/physics_probe_ko.mp4
