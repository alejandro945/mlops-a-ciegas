#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Despliega una versión por anillo, con vuelta atrás si el despliegue falla.
#
#  Uso:  ./demo/deploy.sh 1.0.0 todas        la 1.0.0 a los dos anillos
#        ./demo/deploy.sh 2.0.0 anillo-0     el canario: bomba-01
#        ./demo/deploy.sh 2.0.0 anillo-1     el resto: bomba-02 … 05
#        UMBRAL=0.02 ./demo/deploy.sh 1.0.0 anillo-1     cambia el umbral sin reentrenar
#
#  Cada anillo es un thing group; cada despliegue lleva:
#    failureHandlingPolicy: ROLLBACK   si el componente no arranca, vuelve a la versión anterior
#    jobExecutionsRolloutConfig        despliegue exponencial: 2 bombas por minuto, y se duplica
#    abortConfig                       si falla la mitad, cancela el despliegue
#  Al desplegar la 1.0.0 se guarda /estacion/last_good_version (la usa la Lambda de la vuelta).
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

V="${1:?versión (por ejemplo 1.0.0)}"
ANILLO="${2:?anillo-0 | anillo-1 | todas}"
UMBRAL="${UMBRAL:-}"
[[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "la versión debe verse como 1.0.0 (me diste: $V)"; exit 1; }

REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
COMPONENT="com.estacion.Escucha"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

case "$ANILLO" in
  anillo-0) GRUPOS=(EstacionAnillo0) ;;
  anillo-1) GRUPOS=(EstacionAnillo1) ;;
  todas)    GRUPOS=(EstacionAnillo0 EstacionAnillo1)
            echo "aviso: 'todas' salta el canario. Para la v2 de la demo usa anillo-0 primero." ;;
  *) echo "anillo desconocido: $ANILLO  (anillo-0, anillo-1 o todas)"; exit 1 ;;
esac

aws greengrassv2 describe-component \
  --arn "arn:aws:greengrass:$REGION:$ACCOUNT:components:$COMPONENT:versions:$V" >/dev/null 2>&1 \
  || { echo "la versión $V no está publicada: corre ./demo/publish.sh $V"; exit 1; }

for G in "${GRUPOS[@]}"; do
  # el canario es una sola bomba: basta una falla para cancelar; en el anillo 1, dos
  if [ "$G" = "EstacionAnillo0" ]; then MIN_EJECUTADAS=1; else MIN_EJECUTADAS=2; fi
  python3 - "$V" "arn:aws:iot:$REGION:$ACCOUNT:thinggroup/$G" "deploy-$V-$G-$(date +%s)" \
            "$MIN_EJECUTADAS" "$UMBRAL" > "$TMP/$G.json" <<'PY'
import json, sys
version, target, nombre, min_ejec, umbral = sys.argv[1:6]
# reset [""] = vuelve a la configuración por defecto de ESTA versión (su umbral); luego, el merge opcional
update = {"reset": [""]}
if umbral:
    update["merge"] = json.dumps({"threshold": umbral})
print(json.dumps({
    "targetArn": target,
    "deploymentName": nombre,
    "components": {"com.estacion.Escucha": {"componentVersion": version, "configurationUpdate": update}},
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
                                          "minNumberOfExecutedThings": int(min_ejec)}]},
        "timeoutConfig": {"inProgressTimeoutInMinutes": 10},
    },
}, indent=2))
PY
  ID="$(aws greengrassv2 create-deployment --cli-input-json "file://$TMP/$G.json" --query deploymentId --output text)"
  echo "▶ $COMPONENT $V → $G  (despliegue $ID)  $(date +%H:%M:%S)"
done

if [ "$V" = "1.0.0" ]; then
  aws ssm put-parameter --name /estacion/last_good_version --type String --value 1.0.0 --overwrite >/dev/null
  echo "▶ /estacion/last_good_version = 1.0.0"
fi
echo "Estado:  aws greengrassv2 list-effective-deployments --core-device-thing-name bomba-01 --query 'effectiveDeployments[].[deploymentName,coreDeviceExecutionStatus]' --output table"
