#!/usr/bin/env bash
# Builds talk/MLOps-a-ciegas-DevOpsDays-Bogota-2026.pptx (34 slides + 8 annexes) on top of the official template.
#
#   AWS_ICONS=/path/Icon-package_07312026 bash talk/tools/pptx/render.sh
#
# Steps: rebuild the HTML (build_deck.py) · draw the canvas charts and the memes (render_canvas.js) ·
#        capture the step-by-step diagrams (snap.js + render_html.py) · build the PowerPoint (build_pptx.py).
# Variables:
#   AWS_ICONS            official AWS icon package (default ~/Downloads/Icon-package_07312026)
#   STATION_AUDIO_DIR    folder with pump-a.wav and pump-b.wav (default talk/assets/audio); with audio,
#                        slides 2 and 32 carry a video with sound; without it, «audio pendiente»
#   SKIP_DECK=1          do not rebuild devopsdays.html (use it if you just rebuilt it)
# Requirements: node 18+ · python3 with python-pptx, lxml, cssselect, pillow, cairosvg, weasyprint, numpy, qrcode,
#               fonttools + brotli (macOS: Carlito from talk/assets/fonts) · pdftoppm (poppler) · ffmpeg · pango
set -euo pipefail
cd "$(dirname "$0")"
B=build
export AWS_ICONS="${AWS_ICONS:-$HOME/Downloads/Icon-package_07312026}"
[ -d "$AWS_ICONS" ] || { echo "✘ AWS icons not found in $AWS_ICONS: set AWS_ICONS" >&2; exit 1; }

[ "${SKIP_DECK:-0}" = 1 ] || python3 ../build_deck.py                         # the PowerPoint always comes from the up-to-date HTML
[ -d node_modules ] || npm install --silent
rm -rf "$B" && mkdir -p "$B"
node render_canvas.js ../../devopsdays.html "$B/canvas"                       # charts (cien, tablero) and memes
# step-by-step diagrams: flujo and aws (7 steps each), the PoC architecture and the annex A2 sequence
node snap.js ../../devopsdays.html "$B/steps.json" "flujo:all,aws:all,poc:0,a2:0"
python3 render_html.py "$B/steps.json" "$B/html"
python3 build_pptx.py "$B"
