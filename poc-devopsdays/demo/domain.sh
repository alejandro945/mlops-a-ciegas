#!/usr/bin/env bash
# The pump changes speed (the dataset's shifted domain). No errors at all: the scores drift.
#   ./demo/domain.sh pump-05 shifted     another speed and other background noise
#   ./demo/domain.sh pump-05 normal      back to how it sounded
# Under the hood: writes "shifted" or "normal" to /run/station/mode.
set -euo pipefail
P="${1:?pump (pump-01 … pump-05)}"
MODE="${2:?shifted | normal}"
case "$MODE" in shifted|normal) ;; *) echo "usage: $0 <pump> <shifted|normal>"; exit 1 ;; esac
[[ "$P" =~ ^pump-0[1-5]$ ]] || { echo "unknown pump: $P  (pump-01 … pump-05)"; exit 1; }

docker exec "$P" sh -c 'echo "$1" > /run/station/mode' _ "$MODE"
echo "▶ $P sounds: $MODE  $(date +%H:%M:%S)"
