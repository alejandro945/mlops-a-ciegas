#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  PoC · La estación · levantar la flota
#
#  Red "estacion" + cinco contenedores con el nucleus real de Greengrass.
#    bomba-01        → thing group EstacionAnillo0 (canario)
#    bomba-02 … 05   → thing group EstacionAnillo1
#
#  Uso:  ./fleet/up.sh                 las cinco bombas
#        ./fleet/up.sh --pequeno       cada bomba limitada a un "equipo pequeño"
#        ./fleet/up.sh --recrear       recrea los contenedores (conserva la identidad)
#        REGION=us-east-1 CPUS=2 MEM=2g NUCLEUS_HEAP=192m ./fleet/up.sh
#        DATA=<carpeta>    de dónde sale el audio (por defecto data/estacion, el de model/prepare_data.py)
#
#  Primer arranque, dos caminos:
#    IDENTIDAD=terraform ./fleet/up.sh   las bombas ya existen en AWS (infra/, terraform apply):
#        baja de Parameter Store el certificado de cada una, se lo monta solo durante la
#        instalación y lo borra del disco. Ninguna credencial de AWS entra a los contenedores.
#    ./fleet/up.sh  (IDENTIDAD=instalador)   el instalador de Greengrass registra cada bomba
#        con credenciales TEMPORALES de tu sesión de AWS CLI, que se borran al terminar.
#  Siguientes arranques: sin credenciales; la identidad de cada bomba vive en su volumen <bomba>-gg.
#  Requiere: docker (host Linux), aws cli v2, python3, ./fleet/build.sh, y terraform apply o cloud/setup.sh.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="${REGION:-us-east-1}"
IMAGE="${IMAGE:-estacion/greengrass:latest}"
NETWORK="estacion"
DATA="${DATA:-data/estacion}"
case "$DATA" in /*) ;; *) DATA="$PWD/$DATA" ;; esac
LOGS="$PWD/fleet/logs"
BOOT="$PWD/fleet/.bootstrap"
THING_POLICY="${THING_POLICY_NAME:-EstacionThingPolicy}"
NUCLEUS_HEAP="${NUCLEUS_HEAP-256m}"       # tope del heap de cada nucleus (cada uno es una JVM); vacío = sin tope
ESPERA="${ESPERA:-300}"            # segundos máximos para aprovisionar una bomba
CPUS="${CPUS:-}"; MEM="${MEM:-}"
IDENTIDAD="${IDENTIDAD:-instalador}"     # instalador | terraform
case "$IDENTIDAD" in instalador|terraform) ;; *) echo "IDENTIDAD=$IDENTIDAD no existe: usa instalador o terraform"; exit 1 ;; esac
BOMBAS=(bomba-01 bomba-02 bomba-03 bomba-04 bomba-05)

PEQUENO=0; RECREAR=0
for a in "$@"; do
  case "$a" in
    --pequeno) PEQUENO=1 ;;
    --recrear) RECREAR=1 ;;
    -h|--help) awk 'NR>1 && /^#/ {print} /^set -/ {exit}' "$0"; exit 0 ;;
    *) echo "opción desconocida: $a  (usa --pequeno, --recrear)"; exit 1 ;;
  esac
done
if [ "$PEQUENO" = 1 ]; then CPUS="${CPUS:-1}"; MEM="${MEM:-1g}"; fi

grupo_de() { if [ "$1" = "bomba-01" ]; then echo EstacionAnillo0; else echo EstacionAnillo1; fi; }

[ "$(uname -s)" = "Linux" ] || echo "aviso: AWS pide un host Linux para Greengrass en Docker (este es $(uname -s))."
docker image inspect "$IMAGE" >/dev/null 2>&1 || { echo "falta la imagen $IMAGE: corre ./fleet/build.sh"; exit 1; }
for b in "${BOMBAS[@]}"; do
  [ -d "$DATA/$b" ] || { echo "falta el audio de $b en $DATA/$b"
                         echo "genera los datos con model/prepare_data.py (o apunta DATA= a otro directorio)"; exit 1; }
  # el componente corre como ggc_user, no como root: el audio tiene que ser legible por todos
  chmod -R a+rX "$DATA/$b" 2>/dev/null || echo "aviso: no pude abrir los permisos de lectura de $DATA/$b"
done

# ¿el volumen de la bomba ya tiene identidad (thing, certificado, nucleus instalado)?
aprovisionada() {
  docker volume inspect "$1-gg" >/dev/null 2>&1 &&
  docker run --rm --entrypoint test -v "$1-gg:/greengrass/v2:ro" "$IMAGE" -f /greengrass/v2/.estacion-aprovisionado
}

# Credenciales temporales de tu sesión -> archivo en formato ~/.aws/credentials
escribir_credenciales() {
  mkdir -p "$BOOT"; chmod 700 "$BOOT"
  ( umask 077; python3 - > "$BOOT/credentials" <<'PY'
import configparser, json, os, subprocess, sys
try:
    out = subprocess.run(["aws", "configure", "export-credentials", "--format", "process"],
                         check=True, capture_output=True, text=True).stdout
    c = json.loads(out)
    ak, sk, st = c["AccessKeyId"], c["SecretAccessKey"], c.get("SessionToken")
except Exception:
    ak, sk, st = (os.environ.get("AWS_ACCESS_KEY_ID"), os.environ.get("AWS_SECRET_ACCESS_KEY"),
                  os.environ.get("AWS_SESSION_TOKEN"))
if not ak or not sk:
    sys.exit("no encontré credenciales de AWS (aws configure export-credentials ni variables AWS_*)")
if not st:
    print("aviso: son credenciales de larga duración; mejor usa un rol con sesión temporal.", file=sys.stderr)
cp = configparser.ConfigParser(interpolation=None)
cp["default"] = {"aws_access_key_id": ak, "aws_secret_access_key": sk}
if st:
    cp["default"]["aws_session_token"] = st
cp.write(sys.stdout)
PY
  )
}
# La identidad que creó Terraform (certificado, llave, endpoints) -> $BOOT/<bomba>/, solo para la instalación
escribir_identidad() {   # $1 = bomba
  local b="$1" d="$BOOT/$1"
  mkdir -p "$d"; chmod 700 "$d"
  param() { aws ssm get-parameter --region "$REGION" --name "$1" --with-decryption --query Parameter.Value --output text; }
  ( umask 077
    param "/estacion/bombas/$b/cert" > "$d/device.pem.crt"
    param "/estacion/bombas/$b/key"  > "$d/private.pem.key"
    printf 'IOT_DATA_ENDPOINT=%s\nIOT_CRED_ENDPOINT=%s\n' \
      "$(param /estacion/iot/data_endpoint)" "$(param /estacion/iot/cred_endpoint)" > "$d/endpoints.env" )
  if ! grep -q "BEGIN CERTIFICATE" "$d/device.pem.crt" || ! grep -q "PRIVATE KEY" "$d/private.pem.key"; then
    echo "✘ no encontré la identidad de $b en Parameter Store (/estacion/bombas/$b): ¿corriste terraform apply en infra/?"
    rm -rf "$d"; return 1
  fi
}
trap 'rm -f "$BOOT/credentials"; rm -rf "$BOOT"/bomba-*' EXIT

crear() {   # $1 = bomba · $2 = "con-identidad" en el primer arranque con IDENTIDAD=terraform
  local b="$1" g; g="$(grupo_de "$b")"
  mkdir -p "$LOGS/$b" "$BOOT"; chmod 700 "$BOOT"
  local args=(run -d --name "$b" --hostname "$b" --init --restart unless-stopped --network "$NETWORK"
    --log-driver json-file --log-opt max-size=10m --log-opt max-file=3
    -v "$b-gg:/greengrass/v2"                    # identidad y estado del nucleus
    -v "$LOGS/$b:/greengrass/v2/logs"            # logs del nucleus y del componente, en el host
    -v "$DATA/$b:/data/estacion/$b:ro"           # el audio de la bomba, solo lectura
    -v "$BOOT:/run/aws-bootstrap:ro"             # vacío salvo durante el primer arranque
    -e "AWS_REGION=$REGION" -e "THING_NAME=$b" -e "THING_GROUP_NAME=$g"
    -e "THING_POLICY_NAME=$THING_POLICY")
  if [ "$IDENTIDAD" = terraform ]; then args+=(-e "IDENTIDAD=terraform"); fi
  if [ "${2:-}" = con-identidad ]; then args+=(-v "$BOOT/$b:/run/estacion-id:ro"); fi
  if [ -n "$NUCLEUS_HEAP" ]; then args+=(-e "JAVA_TOOL_OPTIONS=-Xmx${NUCLEUS_HEAP} -XX:+UseSerialGC"); fi
  if [ -n "$CPUS" ]; then args+=(--cpus "$CPUS"); fi
  if [ -n "$MEM" ];  then args+=(--memory "$MEM" --memory-swap "$MEM"); fi
  docker "${args[@]}" "$IMAGE" >/dev/null
}

esperar_aprovisionamiento() {   # $1 = bomba
  local b="$1" i
  for ((i = 0; i < ESPERA; i += 2)); do
    if docker exec "$b" test -f /greengrass/v2/.estacion-aprovisionado 2>/dev/null; then return 0; fi
    if [ "$(docker inspect -f '{{.State.Running}}' "$b" 2>/dev/null || echo false)" != "true" ]; then
      echo "✘ $b se detuvo antes de terminar:"; docker logs --tail 40 "$b" 2>&1 || true; return 1
    fi
    sleep 2
  done
  echo "✘ $b no terminó de aprovisionarse en ${ESPERA} s:"; docker logs --tail 40 "$b" 2>&1 || true
  return 1
}

# ── 1 · red ──────────────────────────────────────────────────────────
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK" >/dev/null
echo "▶ red $NETWORK lista"

# ── 2 · clasificar: qué bombas ya existen y cuáles necesitan identidad ─
PEND=()
for b in "${BOMBAS[@]}"; do
  if [ "$RECREAR" = 1 ] && docker inspect "$b" >/dev/null 2>&1; then docker rm -f "$b" >/dev/null; fi
  if ! aprovisionada "$b"; then
    docker rm -f "$b" >/dev/null 2>&1 || true
    PEND+=("$b"); continue
  fi
  estado="$(docker inspect -f '{{.State.Status}}' "$b" 2>/dev/null || true)"
  case "$estado" in
    running) echo "▶ $b ya corre" ;;
    "")      crear "$b"; echo "▶ $b creada (con su identidad, sin credenciales)" ;;
    *)       docker start "$b" >/dev/null; echo "▶ $b arrancada" ;;
  esac
done

# ── 3 · primer arranque: aprovisionar una por una ────────────────────
if [ "${#PEND[@]}" -gt 0 ] && [ "$IDENTIDAD" = terraform ]; then
  echo "▶ instalando ${PEND[*]} con la identidad de Terraform (sin credenciales de AWS en los contenedores)"
  for b in "${PEND[@]}"; do
    escribir_identidad "$b" || exit 1
    crear "$b" con-identidad
    esperar_aprovisionamiento "$b" || exit 1
    rm -rf "${BOOT:?}/$b"
    echo "✔ $b instalada en $(grupo_de "$b")"
  done
elif [ "${#PEND[@]}" -gt 0 ]; then
  echo "▶ aprovisionando ${PEND[*]} (credenciales temporales; se borran al terminar)"
  escribir_credenciales
  for b in "${PEND[@]}"; do
    crear "$b"
    esperar_aprovisionamiento "$b" || exit 1
    echo "✔ $b aprovisionada en $(grupo_de "$b")"
  done
  rm -f "$BOOT/credentials"
fi

# ── 4 · resumen ──────────────────────────────────────────────────────
echo
docker ps --filter "name=bomba-" --format 'table {{.Names}}\t{{.Status}}'
cat <<EOF

✔ Flota arriba. Cada bomba tarda un par de minutos en aparecer como Healthy.
  aws greengrassv2 list-core-devices --region $REGION --query 'coreDevices[].[coreDeviceThingName,status]' --output table
  logs de una bomba:  tail -f fleet/logs/bomba-03/greengrass.log
Siguiente: ./demo/publish.sh 1.0.0   y   ./demo/deploy.sh 1.0.0 todas
EOF
