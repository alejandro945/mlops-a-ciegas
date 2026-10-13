#!/usr/bin/env bash
# The pump sounds faulty (or goes back to normal). Runs on the machine that has Docker.
#   ./demo/fault.sh pump-03        pump 3 sounds like pump B from the start of the talk
#   ./demo/fault.sh pump-03 off    back to normal
# Under the hood: writes "fault" or "normal" to /run/station/mode; the component re-reads it on every clip.
set -euo pipefail
P="${1:?pump (pump-01 … pump-05)}"
case "${2:-on}" in
  on)  MODE=fault ;;
  off) MODE=normal ;;
  *) echo "usage: $0 <pump> [on|off]"; exit 1 ;;
esac
[[ "$P" =~ ^pump-0[1-5]$ ]] || { echo "unknown pump: $P  (pump-01 … pump-05)"; exit 1; }

docker exec "$P" sh -c 'echo "$1" > /run/station/mode' _ "$MODE"
echo "▶ $P sounds: $MODE  $(date +%H:%M:%S)"
