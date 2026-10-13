#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Deploys a version per ring, with rollback if the deployment fails.
#
#  Usage:  ./demo/deploy.sh 1.0.0 all          1.0.0 to both rings
#          ./demo/deploy.sh 2.0.0 ring-0       the canary: pump-01
#          ./demo/deploy.sh 2.0.0 ring-1       the rest: pump-02 … 05
#          THRESHOLD=0.02 ./demo/deploy.sh 1.0.0 ring-1     changes the threshold without retraining
#
#  Each ring is a thing group; each deployment carries:
#    failureHandlingPolicy: ROLLBACK   if the component does not start, go back to the previous version
#    jobExecutionsRolloutConfig        exponential rollout: 2 pumps per minute, doubling
#    abortConfig                       if half of them fail, cancel the deployment
#  Deploying 1.0.0 stores /station/last_good_version (used by the rollback Lambda).
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

V="${1:?version (for example 1.0.0)}"
RING="${2:?ring-0 | ring-1 | all}"
THRESHOLD="${THRESHOLD:-}"
[[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "the version must look like 1.0.0 (got: $V)"; exit 1; }

REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
COMPONENT="com.station.Listener"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

case "$RING" in
  ring-0) TARGET_GROUPS=(StationRing0) ;;
  ring-1) TARGET_GROUPS=(StationRing1) ;;
  all)    TARGET_GROUPS=(StationRing0 StationRing1)
          echo "warning: 'all' skips the canary. For the demo's v2, use ring-0 first." ;;
  *) echo "unknown ring: $RING  (ring-0, ring-1 or all)"; exit 1 ;;
esac

aws greengrassv2 describe-component \
  --arn "arn:aws:greengrass:$REGION:$ACCOUNT:components:$COMPONENT:versions:$V" >/dev/null 2>&1 \
  || { echo "version $V is not published: run ./demo/publish.sh $V"; exit 1; }

for G in "${TARGET_GROUPS[@]}"; do
  # the canary is a single pump: one failure is enough to cancel; in ring 1, two
  if [ "$G" = "StationRing0" ]; then MIN_EXECUTED=1; else MIN_EXECUTED=2; fi
  python3 - "$V" "arn:aws:iot:$REGION:$ACCOUNT:thinggroup/$G" "deploy-$V-$G-$(date +%s)" \
            "$MIN_EXECUTED" "$THRESHOLD" "$COMPONENT" > "$TMP/$G.json" <<'PY'
import json, sys
version, target, name, min_executed, threshold, component = sys.argv[1:7]
# reset [""] = back to THIS version's default configuration (its threshold); then the optional merge
update = {"reset": [""]}
if threshold:
    update["merge"] = json.dumps({"threshold": threshold})
print(json.dumps({
    "targetArn": target,
    "deploymentName": name,
    "components": {component: {"componentVersion": version, "configurationUpdate": update}},
    "deploymentPolicies": {
        "failureHandlingPolicy": "ROLLBACK",
        "componentUpdatePolicy": {"timeoutInSeconds": 60, "action": "SKIP_NOTIFY_COMPONENTS"},
        "configurationValidationPolicy": {"timeoutInSeconds": 30},
    },
    "iotJobConfiguration": {
        "jobExecutionsRolloutConfig": {
            "exponentialRate": {"baseRatePerMinute": 2, "incrementFactor": 2,
                                "rateIncreaseCriteria": {"numberOfNotifiedThings": 2}},
            "maximumPerMinute": 50,
        },
        "abortConfig": {"criteriaList": [{"failureType": "FAILED", "action": "CANCEL",
                                          "thresholdPercentage": 50,
                                          "minNumberOfExecutedThings": int(min_executed)}]},
        "timeoutConfig": {"inProgressTimeoutInMinutes": 10},
    },
}, indent=2))
PY
  ID="$(aws greengrassv2 create-deployment --cli-input-json "file://$TMP/$G.json" --query deploymentId --output text)"
  echo "▶ $COMPONENT $V → $G  (deployment $ID)  $(date +%H:%M:%S)"
done

if [ "$V" = "1.0.0" ]; then
  aws ssm put-parameter --name /station/last_good_version --type String --value 1.0.0 --overwrite >/dev/null
  echo "▶ /station/last_good_version = 1.0.0"
fi
echo "Status:  aws greengrassv2 list-effective-deployments --core-device-thing-name pump-01 --query 'effectiveDeployments[].[deploymentName,coreDeviceExecutionStatus]' --output table"
