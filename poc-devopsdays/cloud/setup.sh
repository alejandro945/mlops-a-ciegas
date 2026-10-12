#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  PoC · La estación · montaje de la nube (una sola vez; se puede repetir)
#
#  Crea: bucket de artefactos · thing groups EstacionAnillo0 y EstacionAnillo1 ·
#        rol de token exchange (con permiso de leer el bucket) y su alias ·
#        políticas de IoT mínimas · regla estacion_eventos → CloudWatch Logs ·
#        filtros de métrica (namespace Estacion) · dashboard "estacion" ·
#        Lambda estacion-rollback · alarma estacion-fallas-no-oidas · parámetro SSM.
#
#  Requiere: aws cli v2 con permisos de administrador sobre una cuenta de pruebas, python3.
#  Uso:      REGION=us-east-1 ./cloud/setup.sh
#            ALARM_THRESHOLD=8 ./cloud/setup.sh     (fallas no oídas por minuto que disparan la vuelta)
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="${REGION:-us-east-1}"
export AWS_REGION="$REGION" AWS_DEFAULT_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${BUCKET:-estacion-${ACCOUNT}-${REGION}}"
COMPONENT="com.estacion.Escucha"
LOG_GROUP="/estacion/eventos"
NS="Estacion"
RULE="estacion_eventos"
ALARM="estacion-fallas-no-oidas"
FN="estacion-rollback"
PARAM="/estacion/last_good_version"
TES_ROLE="GreengrassV2TokenExchangeRole"
TES_ALIAS="GreengrassCoreTokenExchangeRoleAlias"
THING_POLICY="EstacionThingPolicy"
ALARM_THRESHOLD="${ALARM_THRESHOLD:-8}"
LAMBDA_RUNTIME="${LAMBDA_RUNTIME:-python3.12}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

say()    { printf '\n\033[36m── %s\033[0m\n' "$*"; }
existe() { "$@" >/dev/null 2>&1; }
retry()  { local n=0; until "$@"; do n=$((n + 1)); [ "$n" -ge 6 ] && return 1; echo "  (reintento $n: IAM aún propaga los permisos)"; sleep 5; done; }
llenar() { sed -e "s/__REGION__/$REGION/g" -e "s/__ACCOUNT__/$ACCOUNT/g" -e "s/__BUCKET__/$BUCKET/g" -e "s/__NS__/$NS/g"; }

# Crea la política de IoT, o le pone una versión nueva por defecto (IoT guarda máximo 5)
politica() {   # $1 = nombre · $2 = archivo JSON
  if existe aws iot get-policy --policy-name "$1"; then
    for v in $(aws iot list-policy-versions --policy-name "$1" --query 'policyVersions[?isDefaultVersion==`false`].versionId' --output text); do
      aws iot delete-policy-version --policy-name "$1" --policy-version-id "$v"
    done
    aws iot create-policy-version --policy-name "$1" --policy-document "file://$2" --set-as-default >/dev/null
  else
    aws iot create-policy --policy-name "$1" --policy-document "file://$2" >/dev/null
  fi
}

# Crea un rol con su política de confianza (la actualiza si el rol ya existe)
rol() {   # $1 = nombre · $2 = archivo con la política de confianza
  if existe aws iam get-role --role-name "$1"; then
    aws iam update-assume-role-policy --role-name "$1" --policy-document "file://$2"
  else
    aws iam create-role --role-name "$1" --assume-role-policy-document "file://$2" >/dev/null
  fi
}

say "1 · bucket de artefactos"
if ! existe aws s3api head-bucket --bucket "$BUCKET"; then
  if [ "$REGION" = "us-east-1" ]; then aws s3api create-bucket --bucket "$BUCKET" >/dev/null
  else aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null; fi
fi
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
echo "  s3://$BUCKET"

say "2 · thing groups: un anillo cada uno"
for g in EstacionAnillo0 EstacionAnillo1; do
  existe aws iot describe-thing-group --thing-group-name "$g" || aws iot create-thing-group --thing-group-name "$g" >/dev/null
  echo "  $g"
done

say "3 · identidad de las bombas: rol de token exchange, alias y políticas de IoT"
cat > "$TMP/trust-tes.json" <<'JSON'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"credentials.iot.amazonaws.com"},"Action":"sts:AssumeRole"}]}
JSON
rol "$TES_ROLE" "$TMP/trust-tes.json"
# lo mínimo del rol por defecto del instalador + leer los artefactos de ESTE bucket
llenar > "$TMP/tes-policy.json" <<'JSON'
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents","logs:DescribeLogStreams","s3:GetBucketLocation"],"Resource":"*"},
 {"Effect":"Allow","Action":"s3:GetObject","Resource":"arn:aws:s3:::__BUCKET__/estacion/*"}]}
JSON
aws iam put-role-policy --role-name "$TES_ROLE" --policy-name estacion-dispositivo --policy-document "file://$TMP/tes-policy.json"
existe aws iot describe-role-alias --role-alias "$TES_ALIAS" ||
  retry aws iot create-role-alias --role-alias "$TES_ALIAS" --role-arn "arn:aws:iam::$ACCOUNT:role/$TES_ROLE" >/dev/null

# Política de IoT de las bombas: la mínima de la documentación de Greengrass, con comodín bomba-*
# (Greengrass no admite variables de política de cosa) y permiso de publicar solo en estacion/eventos.
llenar > "$TMP/thing-policy.json" <<'JSON'
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":"iot:Connect","Resource":"arn:aws:iot:__REGION__:__ACCOUNT__:client/bomba-*"},
 {"Effect":"Allow","Action":["iot:Publish","iot:Receive"],"Resource":[
   "arn:aws:iot:__REGION__:__ACCOUNT__:topic/$aws/things/bomba-*/greengrass/health/json",
   "arn:aws:iot:__REGION__:__ACCOUNT__:topic/$aws/things/bomba-*/greengrassv2/health/json",
   "arn:aws:iot:__REGION__:__ACCOUNT__:topic/$aws/things/bomba-*/jobs/*",
   "arn:aws:iot:__REGION__:__ACCOUNT__:topic/$aws/things/bomba-*/shadow/*"]},
 {"Effect":"Allow","Action":"iot:Publish","Resource":"arn:aws:iot:__REGION__:__ACCOUNT__:topic/estacion/eventos"},
 {"Effect":"Allow","Action":"iot:Subscribe","Resource":[
   "arn:aws:iot:__REGION__:__ACCOUNT__:topicfilter/$aws/things/bomba-*/jobs/*",
   "arn:aws:iot:__REGION__:__ACCOUNT__:topicfilter/$aws/things/bomba-*/shadow/*"]},
 {"Effect":"Allow","Action":"iot:AssumeRoleWithCertificate","Resource":"arn:aws:iot:__REGION__:__ACCOUNT__:rolealias/GreengrassCoreTokenExchangeRoleAlias"},
 {"Effect":"Allow","Action":["greengrass:GetComponentVersionArtifact","greengrass:ResolveComponentCandidates","greengrass:GetDeploymentConfiguration","greengrass:ListThingGroupsForCoreDevice"],"Resource":"*"}]}
JSON
politica "$THING_POLICY" "$TMP/thing-policy.json"
# La que el instalador crearía para el alias; la dejamos hecha para que las cinco bombas no compitan por crearla.
llenar > "$TMP/tes-cert-policy.json" <<'JSON'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iot:AssumeRoleWithCertificate","Resource":"arn:aws:iot:__REGION__:__ACCOUNT__:rolealias/GreengrassCoreTokenExchangeRoleAlias"}]}
JSON
politica "GreengrassTESCertificatePolicy$TES_ALIAS" "$TMP/tes-cert-policy.json"
echo "  rol $TES_ROLE · alias $TES_ALIAS · política $THING_POLICY"

say "4 · CloudWatch Logs + regla de IoT"
aws logs create-log-group --log-group-name "$LOG_GROUP" 2>/dev/null || true
aws logs put-retention-policy --log-group-name "$LOG_GROUP" --retention-in-days 7
cat > "$TMP/trust-iot.json" <<JSON
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"iot.amazonaws.com"},"Action":"sts:AssumeRole",
 "Condition":{"StringEquals":{"aws:SourceAccount":"$ACCOUNT"},"ArnLike":{"aws:SourceArn":"arn:aws:iot:$REGION:$ACCOUNT:rule/$RULE"}}}]}
JSON
rol EstacionIotToLogs "$TMP/trust-iot.json"
cat > "$TMP/iot-logs.json" <<JSON
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Action":["logs:CreateLogStream","logs:PutLogEvents","logs:DescribeLogStreams"],
 "Resource":"arn:aws:logs:$REGION:$ACCOUNT:log-group:$LOG_GROUP:*"}]}
JSON
aws iam put-role-policy --role-name EstacionIotToLogs --policy-name logs --policy-document "file://$TMP/iot-logs.json"
# arrived_ts = cuándo llegó a la nube; ts = cuándo decidió la bomba. La diferencia es el tiempo sin red.
cat > "$TMP/rule.json" <<JSON
{"sql":"SELECT *, timestamp() AS arrived_ts FROM 'estacion/eventos'","awsIotSqlVersion":"2016-03-23","ruleDisabled":false,
 "actions":[{"cloudwatchLogs":{"logGroupName":"$LOG_GROUP","roleArn":"arn:aws:iam::$ACCOUNT:role/EstacionIotToLogs"}}]}
JSON
if existe aws iot get-topic-rule --rule-name "$RULE"; then
  retry aws iot replace-topic-rule --rule-name "$RULE" --topic-rule-payload "file://$TMP/rule.json"
else
  retry aws iot create-topic-rule --rule-name "$RULE" --topic-rule-payload "file://$TMP/rule.json"
fi
echo "  regla $RULE → $LOG_GROUP"

say "5 · las señales de la bomba como métricas (namespace $NS)"
# filtro <filtro> <métrica> <patrón> <valor> <dimensiones JSON o -> <valor por defecto o ->
# (CloudWatch no admite valor por defecto en las métricas con dimensiones)
filtro() {
  local t="{\"metricName\":\"$2\",\"metricNamespace\":\"$NS\",\"metricValue\":\"$4\""
  if [ "$5" != "-" ]; then t="$t,\"dimensions\":$5"; fi
  if [ "$6" != "-" ]; then t="$t,\"defaultValue\":$6"; fi
  aws logs put-metric-filter --log-group-name "$LOG_GROUP" --filter-name "$1" \
    --filter-pattern "$3" --metric-transformations "[$t}]"
  echo "  $2"
}
# ¿qué decide?
filtro alertas      Alertas        '{ ($.alert IS TRUE) && ($.device = *) }'              1            '{"Device":"$.device"}'          -
# ¿con cuánta seguridad? (el score contra el umbral de cada versión)
filtro score        Score          '{ ($.score = *) && ($.model_version = *) }'           '$.score'    '{"Version":"$.model_version"}'  -
filtro umbral       Umbral         '{ ($.threshold = *) && ($.model_version = *) }'       '$.threshold' '{"Version":"$.model_version"}' -
# ¿qué versión corre dónde?
filtro inferencias  Inferencias    '{ $.model_version = * }'                              1            '{"Version":"$.model_version"}'  -
# ¿se parece a lo que aprendió?
filtro entrada      InputZ         '{ $.input_z = * }'                                    '$.input_z'  -                                -
# ¿en cuánto tiempo?
filtro latencia     LatencyMs      '{ $.latency_ms = * }'                                 '$.latency_ms' -                              -
# lo que dispara la vuelta: la bomba sonaba con falla (truth solo existe en la demo) y no avisó
filtro fallas       FallasNoOidas  '{ ($.truth = "anomaly") && ($.alert IS FALSE) }'      1            -                                0

say "6 · dashboard estacion"
llenar < cloud/dashboard.json > "$TMP/dashboard.json"
aws cloudwatch put-dashboard --dashboard-name estacion --dashboard-body "file://$TMP/dashboard.json" >/dev/null

say "7 · Lambda estacion-rollback (la vuelta automática)"
cat > "$TMP/trust-lambda.json" <<'JSON'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}
JSON
rol EstacionRollback "$TMP/trust-lambda.json"
aws iam attach-role-policy --role-name EstacionRollback --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
# Mínimo para crear un despliegue de Greengrass (dependientes de greengrass:CreateDeployment) y leer un parámetro
cat > "$TMP/lambda-policy.json" <<JSON
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":"greengrass:CreateDeployment","Resource":"*"},
 {"Effect":"Allow","Action":["iot:CancelJob","iot:CreateJob","iot:DeleteThingShadow","iot:DescribeJob","iot:DescribeThing","iot:DescribeThingGroup","iot:GetThingShadow","iot:UpdateJob","iot:UpdateThingShadow"],
  "Resource":"arn:aws:iot:$REGION:$ACCOUNT:*"},
 {"Effect":"Allow","Action":"ssm:GetParameter","Resource":"arn:aws:ssm:$REGION:$ACCOUNT:parameter$PARAM"}]}
JSON
aws iam put-role-policy --role-name EstacionRollback --policy-name vuelta --policy-document "file://$TMP/lambda-policy.json"
python3 - "$TMP/rollback.zip" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w", zipfile.ZIP_DEFLATED) as z:
    z.write("cloud/rollback_lambda.py", "rollback_lambda.py")
PY
ENV_LAMBDA="Variables={THING_GROUP_ARN=arn:aws:iot:$REGION:$ACCOUNT:thinggroup/EstacionAnillo0,COMPONENT=$COMPONENT,LAST_GOOD_PARAM=$PARAM}"
if existe aws lambda get-function --function-name "$FN"; then
  aws lambda update-function-code --function-name "$FN" --zip-file "fileb://$TMP/rollback.zip" >/dev/null
  aws lambda wait function-updated-v2 --function-name "$FN"
  aws lambda update-function-configuration --function-name "$FN" --timeout 30 --environment "$ENV_LAMBDA" >/dev/null
else
  retry aws lambda create-function --function-name "$FN" --runtime "$LAMBDA_RUNTIME" \
    --handler rollback_lambda.handler --zip-file "fileb://$TMP/rollback.zip" --timeout 30 \
    --role "arn:aws:iam::$ACCOUNT:role/EstacionRollback" --environment "$ENV_LAMBDA" >/dev/null
fi
aws lambda wait function-active-v2 --function-name "$FN"
LAMBDA_ARN="arn:aws:lambda:$REGION:$ACCOUNT:function:$FN"

say "8 · la compuerta: la alarma invoca a la Lambda"
# La alarma solo puede invocar la función si la función se lo permite
aws lambda remove-permission --function-name "$FN" --statement-id cw-alarm 2>/dev/null || true
aws lambda add-permission --function-name "$FN" --statement-id cw-alarm \
  --action lambda:InvokeFunction --principal lambda.alarms.cloudwatch.amazonaws.com \
  --source-account "$ACCOUNT" --source-arn "arn:aws:cloudwatch:$REGION:$ACCOUNT:alarm:$ALARM" >/dev/null
aws cloudwatch put-metric-alarm --alarm-name "$ALARM" \
  --alarm-description "Fallas que ninguna bomba oyó: dispara la vuelta a la última versión buena" \
  --namespace "$NS" --metric-name FallasNoOidas --statistic Sum \
  --period 60 --evaluation-periods 1 --datapoints-to-alarm 1 --threshold "$ALARM_THRESHOLD" \
  --comparison-operator GreaterThanOrEqualToThreshold --treat-missing-data notBreaching \
  --alarm-actions "$LAMBDA_ARN"
echo "  $ALARM (>= $ALARM_THRESHOLD en un minuto) → $FN"

say "9 · última versión buena"
existe aws ssm get-parameter --name "$PARAM" || aws ssm put-parameter --name "$PARAM" --type String --value 1.0.0 >/dev/null
echo "  $PARAM = $(aws ssm get-parameter --name "$PARAM" --query Parameter.Value --output text)"

cat <<EOF

✔ Nube lista.
  bucket      s3://$BUCKET
  anillos     EstacionAnillo0 (canario) · EstacionAnillo1
  regla       $RULE → $LOG_GROUP
  dashboard   https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards/dashboard/estacion
  alarma      $ALARM → $FN → despliegue al anillo 0

Siguiente: en la EC2, ./fleet/build.sh y ./fleet/up.sh   (README, paso 2)
EOF
