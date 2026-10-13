#!/usr/bin/env bash
# What is on screen during the demo: the pumps reporting every decision.
#   pump-03  v1.0.0  ALERT  score 0.82 (threshold 0.50)  input 1.1  4 ms  · arrived 40 s late
#
#   ./demo/watch.sh               all pumps
#   ./demo/watch.sh pump-03       just one
#   SINCE=10m ./demo/watch.sh     starts with the last 10 minutes (default: 1)
set -euo pipefail
REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
HERE="$(cd "$(dirname "$0")" && pwd)"

aws logs tail /station/events --follow --format short --since "${SINCE:-1m}" \
  | python3 -u "$HERE/format_events.py" ${1:+"$1"}
