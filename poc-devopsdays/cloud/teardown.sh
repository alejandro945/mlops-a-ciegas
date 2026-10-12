#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  PoC · La estación · borra TODO lo que creó cloud/setup.sh y la flota
#
#  Uso:  ./cloud/teardown.sh          pide confirmación
#        ./cloud/teardown.sh --yes    sin preguntar
#        REGION=us-east-1 ./cloud/teardown.sh
#  Antes: ./fleet/down.sh en la EC2 (si no, las bombas vuelven a conectarse).
#  Cada paso sigue aunque falle: lo que no exista se salta.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="${REGION:-us-east-1}"
export AWS_REGION="$REGION" AWS_DEFAULT_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${BUCKET:-estacion-${ACCOUNT}-${REGION}}"
COMPONENT="com.estacion.Escucha"
TES_ALIAS="GreengrassCoreTokenExchangeRoleAlias"

if [ "${1:-}" != "--yes" ]; then
  echo "Esto borra en $REGION (cuenta $ACCOUNT): las bombas (things), los anillos, la regla, los logs,"
  echo "las métricas, el dashboard, la alarma, la Lambda, los roles, las políticas, el componente"
  echo "$COMPONENT y el bucket s3://$BUCKET con todo lo que tiene."
  read -r -p "Escribe BORRAR para seguir: " r
  [ "$r" = "BORRAR" ] || { echo "cancelado"; exit 1; }
fi

say() { printf '\n\033[36m── %s\033[0m\n' "$*"; }
# corre el comando; si falla, avisa y sigue
intenta() { "$@" >/dev/null 2>&1 && echo "  ✔ $*" | cut -c1-110 || echo "  · (nada que borrar) $*" | cut -c1-110; }

say "1 · alarma y Lambda"
intenta aws cloudwatch delete-alarms --alarm-names estacion-fallas-no-oidas
intenta aws lambda delete-function --function-name estacion-rollback

say "2 · regla de IoT, logs, métricas y dashboard"
intenta aws iot delete-topic-rule --rule-name estacion_eventos
intenta aws logs delete-log-group --log-group-name /estacion/eventos      # borra también los filtros de métrica
intenta aws cloudwatch delete-dashboards --dashboard-names estacion

say "3 · las bombas en AWS (things, certificados, core devices)"
./cloud/borrar-things.sh bomba-01 bomba-02 bomba-03 bomba-04 bomba-05 || true

say "4 · despliegues y componente de Greengrass"
for g in EstacionAnillo0 EstacionAnillo1; do
  arn="arn:aws:iot:$REGION:$ACCOUNT:thinggroup/$g"
  for d in $(aws greengrassv2 list-deployments --target-arn "$arn" --query 'deployments[].deploymentId' --output text 2>/dev/null || true); do
    intenta aws greengrassv2 cancel-deployment --deployment-id "$d"
    intenta aws greengrassv2 delete-deployment --deployment-id "$d"
  done
done
for c in $(aws greengrassv2 list-component-versions --arn "arn:aws:greengrass:$REGION:$ACCOUNT:components:$COMPONENT" \
             --query 'componentVersions[].arn' --output text 2>/dev/null || true); do
  intenta aws greengrassv2 delete-component --arn "$c"
done

say "5 · thing groups, alias y políticas de IoT"
intenta aws iot delete-thing-group --thing-group-name EstacionAnillo0
intenta aws iot delete-thing-group --thing-group-name EstacionAnillo1
intenta aws iot delete-role-alias --role-alias "$TES_ALIAS"
for p in EstacionThingPolicy "GreengrassTESCertificatePolicy$TES_ALIAS" GreengrassV2IoTThingPolicy; do
  # una política con versiones extra no se borra: primero las no vigentes
  for v in $(aws iot list-policy-versions --policy-name "$p" --query 'policyVersions[?isDefaultVersion==`false`].versionId' --output text 2>/dev/null || true); do
    aws iot delete-policy-version --policy-name "$p" --policy-version-id "$v" >/dev/null 2>&1 || true
  done
  intenta aws iot delete-policy --policy-name "$p"
done

say "6 · roles de IAM"
for r in GreengrassV2TokenExchangeRole EstacionIotToLogs EstacionRollback; do
  for n in $(aws iam list-role-policies --role-name "$r" --query 'PolicyNames[]' --output text 2>/dev/null || true); do
    aws iam delete-role-policy --role-name "$r" --policy-name "$n" >/dev/null 2>&1 || true
  done
  for a in $(aws iam list-attached-role-policies --role-name "$r" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null || true); do
    aws iam detach-role-policy --role-name "$r" --policy-arn "$a" >/dev/null 2>&1 || true
  done
  intenta aws iam delete-role --role-name "$r"
done

say "7 · parámetro y bucket"
intenta aws ssm delete-parameter --name /estacion/last_good_version
intenta aws s3 rb "s3://$BUCKET" --force

echo
echo "✔ Listo. Confirma en Cost Explorer, uno o dos días después, que no queda nada que cobre."
echo "  (La EC2 y sus discos no son de este script: apágala o termínala tú.)"
