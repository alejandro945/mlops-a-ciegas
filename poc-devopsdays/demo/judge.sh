#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  The judge: a candidate model goes on only if, in shadow on the canary, it hears what the
#  active model hears. It never decides before that.
#
#  Usage:  ./demo/judge.sh 2.0.0                 bake 120 s (enough clips for the demo)
#          BAKE=600 MIN_CLIPS=150 ./demo/judge.sh 2.0.0
#
#    1. publishes the carrier if it is not there yet: the last good version (it decides) with the
#       candidate in shadow, as its own component version (1.0.0 + 2.0.0 → 1.1.0)
#    2. starts the state machine station-judge: deploy the carrier to ring 0 → bake → measure in
#       Logs Insights → promote (ring 0, ring 1, last good version) or reject (ring 0 back to the
#       active version alone, and a notification)
#    3. follows the execution until it ends and prints the verdict
#
#  Act 3: run it, then ./demo/fault.sh pump-01 during the bake. The active model alerts, the
#  candidate does not, and the judge rejects it.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

CANDIDATE="${1:?candidate version (for example 2.0.0)}"
[[ "$CANDIDATE" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "the version must look like 2.0.0 (got: $CANDIDATE)"; exit 1; }
BAKE="${BAKE:-120}"
MIN_CLIPS="${MIN_CLIPS:-20}"
MAX_MISSED_RATE="${MAX_MISSED_RATE:-0.1}"
MAX_EXTRA_RATE="${MAX_EXTRA_RATE:-0.2}"

REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
COMPONENT="com.station.Listener"
MACHINE="arn:aws:states:$REGION:$ACCOUNT:stateMachine:station-judge"

ACTIVE="$(aws ssm get-parameter --name /station/last_good_version --query Parameter.Value --output text)"
[ "$ACTIVE" != "$CANDIDATE" ] || { echo "$CANDIDATE is already the last good version"; exit 1; }
IFS=. read -r MAJOR MINOR _ <<< "$ACTIVE"
CARRIER="$MAJOR.$((MINOR + 1)).0"

if ! aws greengrassv2 describe-component \
     --arn "arn:aws:greengrass:$REGION:$ACCOUNT:components:$COMPONENT:versions:$CARRIER" >/dev/null 2>&1; then
  ./demo/publish.sh "$CARRIER" --active "$ACTIVE" --shadow "$CANDIDATE"
fi

INPUT="$(python3 - "$CANDIDATE" "$CARRIER" "$ACTIVE" "$BAKE" "$MIN_CLIPS" "$MAX_MISSED_RATE" "$MAX_EXTRA_RATE" <<'PY'
import json, sys
candidate, carrier, active, bake, min_clips, max_missed, max_extra = sys.argv[1:8]
print(json.dumps({"candidate": candidate, "carrier": carrier, "active": active, "canary": "pump-01",
                  "bakeSeconds": int(bake), "minClips": int(min_clips), "maxMissedRate": float(max_missed),
                  "maxExtraRate": float(max_extra), "maxRounds": 5}))
PY
)"
EXEC="$(aws stepfunctions start-execution --state-machine-arn "$MACHINE" \
          --name "judge-$CANDIDATE-$(date +%s)" --input "$INPUT" --query executionArn --output text)"
echo "▶ judge: $CANDIDATE in shadow on ring 0 ($CARRIER: $ACTIVE decides)  $(date +%H:%M:%S)"
echo "  bake ${BAKE}s · passes if it misses ≤ $MAX_MISSED_RATE of the clips and alerts alone in ≤ $MAX_EXTRA_RATE, over ≥ $MIN_CLIPS clips"
echo "  graph: https://$REGION.console.aws.amazon.com/states/home?region=$REGION#/v2/executions/details/$EXEC"

while :; do
  STATUS="$(aws stepfunctions describe-execution --execution-arn "$EXEC" --query status --output text)"
  [ "$STATUS" = "RUNNING" ] || break
  sleep "${WAIT_SECONDS:-10}"
done

echo "▶ $STATUS  $(date +%H:%M:%S)"
if [ "$STATUS" = "SUCCEEDED" ]; then
  aws stepfunctions describe-execution --execution-arn "$EXEC" --query output --output text
  echo "✔ $CANDIDATE promoted: ring 0, ring 1 and /station/last_good_version"
else
  aws stepfunctions describe-execution --execution-arn "$EXEC" --query '[error,cause]' --output text
  [ "$STATUS" = "FAILED" ] && echo "✘ ring 0 is back on $ACTIVE alone; $CANDIDATE never decided"
  exit 1
fi
