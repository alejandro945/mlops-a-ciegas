#!/usr/bin/env bash
# Genera charla/MLOps-a-ciegas-DevOpsDays-Bogota-2026.pptx (34 láminas + 8 anexos) sobre la plantilla oficial.
#
#   AWS_ICONS=/ruta/Icon-package_07312026 bash charla/tools/pptx/render.sh
#
# Pasos: regenera el HTML (build_deck.py) · dibuja los gráficos de canvas y los memes (render_canvas.js) ·
#        captura los diagramas paso a paso (snap.js + render_html.py) · arma el PowerPoint (build_pptx.py).
# Variables:
#   AWS_ICONS            paquete de íconos oficiales de AWS (por defecto ~/Downloads/Icon-package_07312026)
#   ESTACION_AUDIO_DIR   carpeta con bomba-a.wav y bomba-b.wav (por defecto charla/assets/audio); si hay audio,
#                        las láminas 2 y 32 llevan video con sonido; si no, «audio pendiente»
#   SKIP_DECK=1          no regenera devopsdays.html (úsalo si ya lo regeneraste)
# Requisitos: node 18+ · python3 con python-pptx, lxml, cssselect, pillow, cairosvg, weasyprint, numpy · pdftoppm (poppler) · ffmpeg
set -euo pipefail
cd "$(dirname "$0")"
B=build
export AWS_ICONS="${AWS_ICONS:-$HOME/Downloads/Icon-package_07312026}"
[ -d "$AWS_ICONS" ] || { echo "✘ no encuentro los íconos de AWS en $AWS_ICONS: define AWS_ICONS" >&2; exit 1; }

[ "${SKIP_DECK:-0}" = 1 ] || python3 ../build_deck.py                         # el PowerPoint sale siempre del HTML al día
[ -d node_modules ] || npm install --silent
rm -rf "$B" && mkdir -p "$B"
node render_canvas.js ../../devopsdays.html "$B/canvas"                       # gráficos (cien, tablero) y memes
# diagramas paso a paso: flujo y aws (7 pasos cada uno), la arquitectura de la PoC y la secuencia del anexo A2
node snap.js ../../devopsdays.html "$B/pasos.json" "flujo:all,aws:all,poc:0,a2:0"
python3 render_html.py "$B/pasos.json" "$B/html"
python3 build_pptx.py "$B"
