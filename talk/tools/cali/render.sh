#!/usr/bin/env bash
# Builds talk/techdaycali.html: the Tech Day Cali deck, one self-contained HTML file.
#
#   bash talk/tools/cali/render.sh            REVIEW=1 also screenshots every slide to build/slides/
#
# Steps: the figures (figs.py) and the AWS diagrams (build_arch.py, ARCH_THEME=tdc) as SVG, the
# spectrograms and the QR as PNG · the deck (build_html.py) · with REVIEW=1, Chrome (snap.js).
# Requirements: python3 with numpy, matplotlib, qrcode · the official AWS icons (AWS_ICONS) ·
#               for REVIEW: node 18+ and Google Chrome.
# data.json is committed; to recompute it from a rehearsal: python3 extract.py evidencia-e2e/<date>
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
export AWS_ICONS="${AWS_ICONS:-$HOME/Downloads/Icon-package_07312026}"
[ -d "$AWS_ICONS" ] || { echo "✘ AWS icons not found in $AWS_ICONS: set AWS_ICONS" >&2; exit 1; }
rm -rf build && mkdir -p build/svg build/png
"$PY" figs.py build/svg
ARCH_THEME=tdc "$PY" - <<'PY'
import re, sys
sys.path.insert(0, "..")
import build_arch as A
for mode, name in (("poc", "arch-poc"), ("ref", "arch-ref")):
    s = A.build(mode, deck=True)
    s = s.replace('width="1600" height="900" viewBox="0 0 1600 900"',
                  'width="1440" height="690" viewBox="80 140 1440 690" style="background:#fff"', 1)
    open(f"build/svg/{name}.svg", "w").write(s)
PY
rm -f build/svg/qr.svg
"$PY" build_html.py
if [ "${REVIEW:-0}" = 1 ]; then
  [ -d node_modules ] || npm install --silent
  node snap.js ../../techdaycali.html build/slides
fi
