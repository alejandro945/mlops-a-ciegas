#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  PoC · The station · deletes EVERYTHING cloud/setup.sh and the fleet created
#
#  Usage:  ./cloud/teardown.sh          asks for confirmation
#          ./cloud/teardown.sh --yes    no questions asked
#          REGION=us-east-1 ./cloud/teardown.sh
#  First: ./fleet/down.sh on the EC2 (otherwise the pumps connect again).
#  Every step goes on even if it fails: whatever does not exist is skipped.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="${REGION:-us-east-1}"
export AWS_REGION="$REGION" AWS_DEFAULT_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${BUCKET:-station-${ACCOUNT}-${REGION}}"
COMPONENT="com.station.Listener"
TES_ALIAS="GreengrassCoreTokenExchangeRoleAlias"

if [ "${1:-}" != "--yes" ]; then
  echo "This deletes in $REGION (account $ACCOUNT): the pumps (things), the rings, the rule, the logs,"
  echo "the metrics, the dashboard, the alarm, the Lambda, the roles, the policies, the component"
  echo "$COMPONENT and the bucket s3://$BUCKET with everything in it."
  read -r -p "Type DELETE to continue: " r
  [ "$r" = "DELETE" ] || { echo "cancelled"; exit 1; }
fi

say() { printf '\n\033[36m── %s\033[0m\n' "$*"; }
# runs the command; if it fails, says so and moves on
try() { "$@" >/dev/null 2>&1 && echo "  ✔ $*" | cut -c1-110 || echo "  · (nothing to delete) $*" | cut -c1-110; }

say "1 · alarm and Lambda"
try aws cloudwatch delete-alarms --alarm-names station-missed-faults
try aws lambda delete-function --function-name station-rollback

say "2 · IoT rule, logs, metrics and dashboard"
try aws iot delete-topic-rule --rule-name station_events
try aws logs delete-log-group --log-group-name /station/events      # also deletes the metric filters
try aws cloudwatch delete-dashboards --dashboard-names station

say "3 · the pumps in AWS (things, certificates, core devices)"
./cloud/delete-things.sh pump-01 pump-02 pump-03 pump-04 pump-05 || true

say "4 · Greengrass deployments and component"
for g in StationRing0 StationRing1; do
  arn="arn:aws:iot:$REGION:$ACCOUNT:thinggroup/$g"
  for d in $(aws greengrassv2 list-deployments --target-arn "$arn" --query 'deployments[].deploymentId' --output text 2>/dev/null || true); do
    try aws greengrassv2 cancel-deployment --deployment-id "$d"
    try aws greengrassv2 delete-deployment --deployment-id "$d"
  done
done
for c in $(aws greengrassv2 list-component-versions --arn "arn:aws:greengrass:$REGION:$ACCOUNT:components:$COMPONENT" \
             --query 'componentVersions[].arn' --output text 2>/dev/null || true); do
  try aws greengrassv2 delete-component --arn "$c"
done

say "5 · thing groups, alias and IoT policies"
try aws iot delete-thing-group --thing-group-name StationRing0
try aws iot delete-thing-group --thing-group-name StationRing1
try aws iot delete-role-alias --role-alias "$TES_ALIAS"
for p in StationThingPolicy "GreengrassTESCertificatePolicy$TES_ALIAS" GreengrassV2IoTThingPolicy; do
  # a policy with extra versions cannot be deleted: first the non-default ones
  for v in $(aws iot list-policy-versions --policy-name "$p" --query 'policyVersions[?isDefaultVersion==`false`].versionId' --output text 2>/dev/null || true); do
    aws iot delete-policy-version --policy-name "$p" --policy-version-id "$v" >/dev/null 2>&1 || true
  done
  try aws iot delete-policy --policy-name "$p"
done

say "6 · IAM roles"
for r in GreengrassV2TokenExchangeRole StationIotToLogs StationRollback; do
  for n in $(aws iam list-role-policies --role-name "$r" --query 'PolicyNames[]' --output text 2>/dev/null || true); do
    aws iam delete-role-policy --role-name "$r" --policy-name "$n" >/dev/null 2>&1 || true
  done
  for a in $(aws iam list-attached-role-policies --role-name "$r" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null || true); do
    aws iam detach-role-policy --role-name "$r" --policy-arn "$a" >/dev/null 2>&1 || true
  done
  try aws iam delete-role --role-name "$r"
done

say "7 · parameter and bucket"
try aws ssm delete-parameter --name /station/last_good_version
try aws s3 rb "s3://$BUCKET" --force

echo
echo "✔ Done. Check Cost Explorer a day or two later to confirm nothing is still billing."
echo "  (The EC2 and its disks are not this script's job: stop or terminate it yourself.)"
