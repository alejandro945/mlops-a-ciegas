#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Publica una versión del modelo como versión del componente com.estacion.Escucha
#    1. sube build/<versión>/{inference.py,features.py,model.onnx,stats.json}
#       a s3://estacion-<cuenta>-<región>/estacion/<versión>/
#    2. crea la versión del componente desde la receta, con el umbral de stats.json
#
#  Uso:  ./demo/publish.sh 1.0.0
#        ./demo/publish.sh 1.0.0 --allow-synthetic     (solo para probar la tubería)
#
#  Una versión publicada no se toca: Greengrass calcula el digest de cada artefacto al
#  crearla. Para cambiar algo, sube una versión nueva.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

V="${1:?versión (por ejemplo 1.0.0)}"; shift || true
PERMITIR_SINTETICO=0
for a in "$@"; do
  case "$a" in
    --allow-synthetic) PERMITIR_SINTETICO=1 ;;
    *) echo "opción desconocida: $a  (usa --allow-synthetic)"; exit 1 ;;
  esac
done
[[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "la versión debe verse como 1.0.0 (me diste: $V)"; exit 1; }

REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${BUCKET:-estacion-${ACCOUNT}-${REGION}}"
COMPONENT="com.estacion.Escucha"
SRC="build/$V"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

for f in inference.py features.py model.onnx stats.json; do
  [ -f "$SRC/$f" ] || { echo "falta $SRC/$f  (entrena con model/train.py; mira model/README.md)"; exit 1; }
done

# umbral, ¿sintético?, y que stats.json hable de este modelo y de esta versión
INFO="$(python3 - "$SRC" "$V" <<'PY'
import hashlib, json, sys
src, v = sys.argv[1:3]
st = json.load(open(f"{src}/stats.json"))
if "threshold" not in st:
    sys.exit("stats.json no trae el campo threshold")
if st.get("version") not in (None, v):
    sys.exit(f"stats.json es de la versión {st['version']}, no de {v}")
sha = hashlib.sha256(open(f"{src}/model.onnx", "rb").read()).hexdigest()
if st.get("sha256") not in (None, sha):
    sys.exit("el sha256 de stats.json no es el de model.onnx: reentrena o copia los archivos completos")
print(st["threshold"], 1 if st.get("synthetic") else 0)
PY
)"
UMBRAL="${INFO% *}"; SINTETICO="${INFO##* }"

if [ "$SINTETICO" = "1" ] && [ "$PERMITIR_SINTETICO" != "1" ]; then
  echo "✘ $SRC/stats.json dice \"synthetic\": true. Ese modelo aprendió con audio sintético:"
  echo "  sirve para probar la tubería, no para mostrar cifras. Si es lo que quieres: --allow-synthetic"
  exit 1
fi
[ "$SINTETICO" = "1" ] && echo "aviso: modelo sintético (--allow-synthetic). Ninguna cifra de esta corrida va a una lámina."

aws s3api head-bucket --bucket "$BUCKET" >/dev/null 2>&1 || { echo "no existe s3://$BUCKET: corre ./cloud/setup.sh"; exit 1; }

ARN="arn:aws:greengrass:$REGION:$ACCOUNT:components:$COMPONENT:versions:$V"
if aws greengrassv2 describe-component --arn "$ARN" >/dev/null 2>&1; then
  echo "▶ $COMPONENT $V ya está publicada: no la toco (los artefactos son inmutables)."
  echo "  Para cambiar algo, sube una versión nueva."
  exit 0
fi

echo "▶ subiendo $SRC a s3://$BUCKET/estacion/$V/"
for f in inference.py features.py model.onnx stats.json; do
  aws s3 cp "$SRC/$f" "s3://$BUCKET/estacion/$V/$f" --only-show-errors
done

sed -e "s/__VERSION__/$V/g" -e "s/__BUCKET__/$BUCKET/g" -e "s/__THRESHOLD__/$UMBRAL/g" \
  component/recipe.template.yaml > "$TMP/recipe.yaml"

echo "▶ creando $COMPONENT $V (umbral $UMBRAL)"
aws greengrassv2 create-component-version --inline-recipe "fileb://$TMP/recipe.yaml" \
  --query '[componentName,componentVersion,status.componentState]' --output text

# Greengrass calcula el digest de cada artefacto; la versión queda DEPLOYABLE cuando termina
for _ in $(seq 1 30); do
  ESTADO="$(aws greengrassv2 describe-component --arn "$ARN" --query status.componentState --output text)"
  [ "$ESTADO" = "REQUESTED" ] || break
  sleep 2
done
if [ "$ESTADO" != "DEPLOYABLE" ]; then
  echo "✘ la versión quedó en $ESTADO"
  aws greengrassv2 describe-component --arn "$ARN" --query status.message --output text || true
  exit 1
fi
echo "✔ $COMPONENT $V lista para desplegar"
echo "Siguiente: ./demo/deploy.sh $V todas     (o anillo-0 / anillo-1)"
