#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  PoC · The station · cloud setup (once; safe to repeat)
#
#  Creates: artifacts bucket · thing groups StationRing0 and StationRing1 ·
#           token exchange role (allowed to read the bucket) and its alias ·
#           minimal IoT policies · rule station_events → CloudWatch Logs ·
#           metric filters (namespace Station) · dashboard "station" ·
#           Lambda station-rollback · alarm station-missed-faults · SSM parameter.
#
#  Requires: aws cli v2 with administrator permissions on a test account, python3.
#  Usage:    REGION=us-east-1 ./cloud/setup.sh
#            ALARM_THRESHOLD=8 ./cloud/setup.sh     (missed faults per minute that trigger the rollback)
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="${REGION:-us-east-1}"
export AWS_REGION="$REGION" AWS_DEFAULT_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${BUCKET:-station-${ACCOUNT}-${REGION}}"
COMPONENT="com.station.Listener"
LOG_GROUP="/station/events"
NS="Station"
RULE="station_events"
ALARM="station-missed-faults"
FN="station-rollback"
PARAM="/station/last_good_version"
TES_ROLE="GreengrassV2TokenExchangeRole"
TES_ALIAS="GreengrassCoreTokenExchangeRoleAlias"
THING_POLICY="StationThingPolicy"
ALARM_THRESHOLD="${ALARM_THRESHOLD:-8}"
LAMBDA_RUNTIME="${LAMBDA_RUNTIME:-python3.12}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

say()    { printf '\n\033[36m── %s\033[0m\n' "$*"; }
exists() { "$@" >/dev/null 2>&1; }
retry()  { local n=0; until "$@"; do n=$((n + 1)); [ "$n" -ge 6 ] && return 1; echo "  (retry $n: IAM is still propagating permissions)"; sleep 5; done; }
fill()   { sed -e "s/__REGION__/$REGION/g" -e "s/__ACCOUNT__/$ACCOUNT/g" -e "s/__BUCKET__/$BUCKET/g" -e "s/__NS__/$NS/g"; }

# Creates the IoT policy, or gives it a new default version (IoT keeps at most 5)
iot_policy() {   # $1 = name · $2 = JSON file
  if exists aws iot get-policy --policy-name "$1"; then
    for v in $(aws iot list-policy-versions --policy-name "$1" --query 'policyVersions[?isDefaultVersion==`false`].versionId' --output text); do
      aws iot delete-policy-version --policy-name "$1" --policy-version-id "$v"
    done
    aws iot create-policy-version --policy-name "$1" --policy-document "file://$2" --set-as-default >/dev/null
  else
    aws iot create-policy --policy-name "$1" --policy-document "file://$2" >/dev/null
  fi
}

# Creates a role with its trust policy (updates the trust policy if the role already exists)
role() {   # $1 = name · $2 = file with the trust policy
  if exists aws iam get-role --role-name "$1"; then
    aws iam update-assume-role-policy --role-name "$1" --policy-document "file://$2"
  else
    aws iam create-role --role-name "$1" --assume-role-policy-document "file://$2" >/dev/null
  fi
}

say "1 · artifacts bucket"
if ! exists aws s3api head-bucket --bucket "$BUCKET"; then
  if [ "$REGION" = "us-east-1" ]; then aws s3api create-bucket --bucket "$BUCKET" >/dev/null
  else aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null; fi
fi
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
echo "  s3://$BUCKET"

say "2 · thing groups: one per ring"
for g in StationRing0 StationRing1; do
  exists aws iot describe-thing-group --thing-group-name "$g" || aws iot create-thing-group --thing-group-name "$g" >/dev/null
  echo "  $g"
done

say "3 · pump identity: token exchange role, alias and IoT policies"
cat > "$TMP/trust-tes.json" <<'JSON'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"credentials.iot.amazonaws.com"},"Action":"sts:AssumeRole"}]}
JSON
role "$TES_ROLE" "$TMP/trust-tes.json"
# the minimum of the installer's default role + read the artifacts in THIS bucket
fill > "$TMP/tes-policy.json" <<'JSON'
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents","logs:DescribeLogStreams","s3:GetBucketLocation"],"Resource":"*"},
 {"Effect":"Allow","Action":"s3:GetObject","Resource":"arn:aws:s3:::__BUCKET__/station/*"}]}
JSON
aws iam put-role-policy --role-name "$TES_ROLE" --policy-name station-device --policy-document "file://$TMP/tes-policy.json"
exists aws iot describe-role-alias --role-alias "$TES_ALIAS" ||
  retry aws iot create-role-alias --role-alias "$TES_ALIAS" --role-arn "arn:aws:iam::$ACCOUNT:role/$TES_ROLE" >/dev/null

# The pumps' IoT policy: the minimal one from the Greengrass docs, with a pump-* wildcard
# (Greengrass does not support thing policy variables) and permission to publish only to station/events.
fill > "$TMP/thing-policy.json" <<'JSON'
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":"iot:Connect","Resource":"arn:aws:iot:__REGION__:__ACCOUNT__:client/pump-*"},
 {"Effect":"Allow","Action":["iot:Publish","iot:Receive"],"Resource":[
   "arn:aws:iot:__REGION__:__ACCOUNT__:topic/$aws/things/pump-*/greengrass/health/json",
   "arn:aws:iot:__REGION__:__ACCOUNT__:topic/$aws/things/pump-*/greengrassv2/health/json",
   "arn:aws:iot:__REGION__:__ACCOUNT__:topic/$aws/things/pump-*/jobs/*",
   "arn:aws:iot:__REGION__:__ACCOUNT__:topic/$aws/things/pump-*/shadow/*"]},
 {"Effect":"Allow","Action":"iot:Publish","Resource":"arn:aws:iot:__REGION__:__ACCOUNT__:topic/station/events"},
 {"Effect":"Allow","Action":"iot:Subscribe","Resource":[
   "arn:aws:iot:__REGION__:__ACCOUNT__:topicfilter/$aws/things/pump-*/jobs/*",
   "arn:aws:iot:__REGION__:__ACCOUNT__:topicfilter/$aws/things/pump-*/shadow/*"]},
 {"Effect":"Allow","Action":"iot:AssumeRoleWithCertificate","Resource":"arn:aws:iot:__REGION__:__ACCOUNT__:rolealias/GreengrassCoreTokenExchangeRoleAlias"},
 {"Effect":"Allow","Action":["greengrass:GetComponentVersionArtifact","greengrass:ResolveComponentCandidates","greengrass:GetDeploymentConfiguration","greengrass:ListThingGroupsForCoreDevice"],"Resource":"*"}]}
JSON
iot_policy "$THING_POLICY" "$TMP/thing-policy.json"
# The one the installer would create for the alias; created up front so the five pumps don't race to create it.
fill > "$TMP/tes-cert-policy.json" <<'JSON'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iot:AssumeRoleWithCertificate","Resource":"arn:aws:iot:__REGION__:__ACCOUNT__:rolealias/GreengrassCoreTokenExchangeRoleAlias"}]}
JSON
iot_policy "GreengrassTESCertificatePolicy$TES_ALIAS" "$TMP/tes-cert-policy.json"
echo "  role $TES_ROLE · alias $TES_ALIAS · policy $THING_POLICY"

say "4 · CloudWatch Logs + IoT rule"
aws logs create-log-group --log-group-name "$LOG_GROUP" 2>/dev/null || true
aws logs put-retention-policy --log-group-name "$LOG_GROUP" --retention-in-days 7
cat > "$TMP/trust-iot.json" <<JSON
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"iot.amazonaws.com"},"Action":"sts:AssumeRole",
 "Condition":{"StringEquals":{"aws:SourceAccount":"$ACCOUNT"},"ArnLike":{"aws:SourceArn":"arn:aws:iot:$REGION:$ACCOUNT:rule/$RULE"}}}]}
JSON
role StationIotToLogs "$TMP/trust-iot.json"
cat > "$TMP/iot-logs.json" <<JSON
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Action":["logs:CreateLogStream","logs:PutLogEvents","logs:DescribeLogStreams"],
 "Resource":"arn:aws:logs:$REGION:$ACCOUNT:log-group:$LOG_GROUP:*"}]}
JSON
aws iam put-role-policy --role-name StationIotToLogs --policy-name logs --policy-document "file://$TMP/iot-logs.json"
# arrived_ts = when it reached the cloud; ts = when the pump decided. The difference is the time without network.
cat > "$TMP/rule.json" <<JSON
{"sql":"SELECT *, timestamp() AS arrived_ts FROM 'station/events'","awsIotSqlVersion":"2016-03-23","ruleDisabled":false,
 "actions":[{"cloudwatchLogs":{"logGroupName":"$LOG_GROUP","roleArn":"arn:aws:iam::$ACCOUNT:role/StationIotToLogs"}}]}
JSON
if exists aws iot get-topic-rule --rule-name "$RULE"; then
  retry aws iot replace-topic-rule --rule-name "$RULE" --topic-rule-payload "file://$TMP/rule.json"
else
  retry aws iot create-topic-rule --rule-name "$RULE" --topic-rule-payload "file://$TMP/rule.json"
fi
echo "  rule $RULE → $LOG_GROUP"

say "5 · the pump's signals as metrics (namespace $NS)"
# metric_filter <filter> <metric> <pattern> <value> <dimensions JSON or -> <default value or ->
# (CloudWatch does not allow a default value on metrics with dimensions)
metric_filter() {
  local t="{\"metricName\":\"$2\",\"metricNamespace\":\"$NS\",\"metricValue\":\"$4\""
  if [ "$5" != "-" ]; then t="$t,\"dimensions\":$5"; fi
  if [ "$6" != "-" ]; then t="$t,\"defaultValue\":$6"; fi
  aws logs put-metric-filter --log-group-name "$LOG_GROUP" --filter-name "$1" \
    --filter-pattern "$3" --metric-transformations "[$t}]"
  echo "  $2"
}
# what does it decide?
metric_filter alerts         Alerts        '{ ($.alert IS TRUE) && ($.device = *) }'              1             '{"Device":"$.device"}'          -
# how confident? (the score against each version's threshold)
metric_filter score          Score         '{ ($.score = *) && ($.model_version = *) }'           '$.score'     '{"Version":"$.model_version"}'  -
metric_filter threshold      Threshold     '{ ($.threshold = *) && ($.model_version = *) }'       '$.threshold' '{"Version":"$.model_version"}'  -
# which version runs where?
metric_filter inferences     Inferences    '{ $.model_version = * }'                              1             '{"Version":"$.model_version"}'  -
# does it look like what it learned?
metric_filter input          InputZ        '{ $.input_z = * }'                                    '$.input_z'   -                                -
metric_filter input_by_device InputZ       '{ ($.input_z = *) && ($.device = *) }'                '$.input_z'   '{"Device":"$.device"}'          -
# how fast?
metric_filter latency        LatencyMs     '{ $.latency_ms = * }'                                 '$.latency_ms' -                               -
# what triggers the rollback: the pump sounded faulty (truth only exists in the demo) and did not alert
metric_filter missed_faults  MissedFaults  '{ ($.truth = "anomaly") && ($.alert IS FALSE) }'      1             -                                0

say "6 · dashboard station"
fill < cloud/dashboard.json > "$TMP/dashboard.json"
aws cloudwatch put-dashboard --dashboard-name station --dashboard-body "file://$TMP/dashboard.json" >/dev/null

say "7 · Lambda station-rollback (the automatic rollback)"
cat > "$TMP/trust-lambda.json" <<'JSON'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}
JSON
role StationRollback "$TMP/trust-lambda.json"
aws iam attach-role-policy --role-name StationRollback --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
# The minimum to create a Greengrass deployment (dependent actions of greengrass:CreateDeployment) and read a parameter
cat > "$TMP/lambda-policy.json" <<JSON
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":"greengrass:CreateDeployment","Resource":"*"},
 {"Effect":"Allow","Action":["iot:CancelJob","iot:CreateJob","iot:DeleteThingShadow","iot:DescribeJob","iot:DescribeThing","iot:DescribeThingGroup","iot:GetThingShadow","iot:UpdateJob","iot:UpdateThingShadow"],
  "Resource":"arn:aws:iot:$REGION:$ACCOUNT:*"},
 {"Effect":"Allow","Action":"ssm:GetParameter","Resource":"arn:aws:ssm:$REGION:$ACCOUNT:parameter$PARAM"}]}
JSON
aws iam put-role-policy --role-name StationRollback --policy-name rollback --policy-document "file://$TMP/lambda-policy.json"
python3 - "$TMP/rollback.zip" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w", zipfile.ZIP_DEFLATED) as z:
    z.write("cloud/rollback_lambda.py", "rollback_lambda.py")
PY
ENV_LAMBDA="Variables={THING_GROUP_ARN=arn:aws:iot:$REGION:$ACCOUNT:thinggroup/StationRing0,COMPONENT=$COMPONENT,LAST_GOOD_PARAM=$PARAM}"
if exists aws lambda get-function --function-name "$FN"; then
  aws lambda update-function-code --function-name "$FN" --zip-file "fileb://$TMP/rollback.zip" >/dev/null
  aws lambda wait function-updated-v2 --function-name "$FN"
  aws lambda update-function-configuration --function-name "$FN" --timeout 30 --environment "$ENV_LAMBDA" >/dev/null
else
  retry aws lambda create-function --function-name "$FN" --runtime "$LAMBDA_RUNTIME" \
    --handler rollback_lambda.handler --zip-file "fileb://$TMP/rollback.zip" --timeout 30 \
    --role "arn:aws:iam::$ACCOUNT:role/StationRollback" --environment "$ENV_LAMBDA" >/dev/null
fi
aws lambda wait function-active-v2 --function-name "$FN"
LAMBDA_ARN="arn:aws:lambda:$REGION:$ACCOUNT:function:$FN"

say "8 · the gate: the alarm invokes the Lambda"
# The alarm can only invoke the function if the function allows it
aws lambda remove-permission --function-name "$FN" --statement-id cw-alarm 2>/dev/null || true
aws lambda add-permission --function-name "$FN" --statement-id cw-alarm \
  --action lambda:InvokeFunction --principal lambda.alarms.cloudwatch.amazonaws.com \
  --source-account "$ACCOUNT" --source-arn "arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:$ALARM" >/dev/null
aws cloudwatch put-metric-alarm --alarm-name "$ALARM" \
  --alarm-description "Faults no pump heard: rolls back to the last good version" \
  --namespace "$NS" --metric-name MissedFaults --statistic Sum \
  --period 60 --evaluation-periods 1 --datapoints-to-alarm 1 --threshold "$ALARM_THRESHOLD" \
  --comparison-operator GreaterThanOrEqualToThreshold --treat-missing-data notBreaching \
  --alarm-actions "$LAMBDA_ARN"
echo "  $ALARM (>= $ALARM_THRESHOLD in one minute) → $FN"

say "9 · last good version"
exists aws ssm get-parameter --name "$PARAM" || aws ssm put-parameter --name "$PARAM" --type String --value 1.0.0 >/dev/null
echo "  $PARAM = $(aws ssm get-parameter --name "$PARAM" --query Parameter.Value --output text)"

cat <<EOF2

✔ Cloud ready.
  bucket      s3://$BUCKET
  rings       StationRing0 (canary) · StationRing1
  rule        $RULE → $LOG_GROUP
  dashboard   https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards/dashboard/station
  alarm       $ALARM → $FN → deployment to ring 0

Next: on the EC2, ./fleet/build.sh and ./fleet/up.sh   (README, step 3)
EOF2
