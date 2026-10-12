#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Entrypoint de la bomba (imagen estacion/greengrass)
#
#  Primer arranque : IDENTIDAD=instalador (por defecto) → aprovisiona la bomba
#                    (thing, thing group, rol de token exchange) con credenciales
#                    temporales montadas en /run/aws-bootstrap/credentials.
#                    IDENTIDAD=terraform → la bomba ya existe en AWS (infra/):
#                    instala el nucleus con el certificado montado en
#                    /run/estacion-id, sin ninguna credencial de AWS.
#  Siguientes      : no hay credenciales; la identidad ya vive en el volumen
#                    /greengrass/v2 y solo arranca el nucleus.
#
#  El nucleus queda en primer plano (PID 1 bajo docker --init).
#  Variables: THING_NAME, THING_GROUP_NAME, AWS_REGION, THING_POLICY_NAME,
#             TES_ROLE_NAME, TES_ROLE_ALIAS_NAME, COMPONENT_DEFAULT_USER,
#             IDENTIDAD (instalador|terraform), ID_DIR, GREENGRASS_VERSION.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="${GGC_ROOT_PATH:-/greengrass/v2}"
MARCA="$ROOT/.estacion-aprovisionado"
LOADER="$ROOT/alts/current/distro/bin/loader"
CREDS="${CREDS_FILE:-/run/aws-bootstrap/credentials}"
INSTALADOR="${INSTALLER_JAR:-/opt/greengrass-installer/lib/Greengrass.jar}"
MODO_DIR="${ESTACION_RUN_DIR:-/run/estacion}"
ID_DIR="${ID_DIR:-/run/estacion-id}"
CA_RAIZ="${CA_RAIZ:-/opt/greengrass-installer/AmazonRootCA1.pem}"
IDENTIDAD="${IDENTIDAD:-instalador}"
log() { echo "[estacion] $*"; }

# Lo que la bomba "oye": la demo escribe este archivo con docker exec (como root);
# el componente lo relee en cada clip. Se conserva si el contenedor se reinicia.
mkdir -p "$MODO_DIR"
[ -f "$MODO_DIR/modo" ] || echo normal > "$MODO_DIR/modo"
chmod 755 "$MODO_DIR"
chmod 644 "$MODO_DIR/modo"

# Para depurar:  docker run --rm -it estacion/greengrass bash
if [ "$#" -gt 0 ]; then exec "$@"; fi

aprovisionar() {
  : "${THING_NAME:?falta THING_NAME}"
  : "${THING_GROUP_NAME:?falta THING_GROUP_NAME}"
  : "${AWS_REGION:?falta AWS_REGION}"
  if [ ! -r "$CREDS" ]; then
    log "esta bomba no tiene identidad y no hay credenciales en $CREDS."
    log "levántala con ./fleet/up.sh (él monta las credenciales temporales)."
    exit 1
  fi

  # Las credenciales viven solo en este subproceso: el nucleus arranca sin ellas.
  eval "$(python3 - "$CREDS" <<'PY'
import configparser, shlex, sys
c = configparser.ConfigParser(interpolation=None)
c.read(sys.argv[1])
s = c["default"]
print("export AWS_ACCESS_KEY_ID=" + shlex.quote(s["aws_access_key_id"]))
print("export AWS_SECRET_ACCESS_KEY=" + shlex.quote(s["aws_secret_access_key"]))
if s.get("aws_session_token"):
    print("export AWS_SESSION_TOKEN=" + shlex.quote(s["aws_session_token"]))
PY
)"
  [ -n "${AWS_ACCESS_KEY_ID:-}" ] || { log "no pude leer las credenciales de $CREDS"; exit 1; }

  log "primer arranque: aprovisionando $THING_NAME en $THING_GROUP_NAME ($AWS_REGION)"
  java -Droot="$ROOT" -Dlog.store=FILE \
    -jar "$INSTALADOR" \
    --aws-region "$AWS_REGION" \
    --thing-name "$THING_NAME" \
    --thing-group-name "$THING_GROUP_NAME" \
    --thing-policy-name "${THING_POLICY_NAME:-GreengrassV2IoTThingPolicy}" \
    --tes-role-name "${TES_ROLE_NAME:-GreengrassV2TokenExchangeRole}" \
    --tes-role-alias-name "${TES_ROLE_ALIAS_NAME:-GreengrassCoreTokenExchangeRoleAlias}" \
    --component-default-user "${COMPONENT_DEFAULT_USER:-ggc_user:ggc_group}" \
    --provision true \
    --setup-system-service false \
    --start false
}

# La bomba ya existe en AWS (Terraform creó thing, certificado, política y anillo):
# solo se instala el nucleus con ese certificado. Ninguna credencial de AWS entra al contenedor.
instalar_con_identidad() {
  : "${THING_NAME:?falta THING_NAME}"
  : "${AWS_REGION:?falta AWS_REGION}"
  local f
  for f in device.pem.crt private.pem.key endpoints.env; do
    if [ ! -r "$ID_DIR/$f" ]; then
      log "falta $ID_DIR/$f: esta bomba no tiene su identidad montada."
      log "levántala con IDENTIDAD=terraform ./fleet/up.sh (él la baja de Parameter Store)."
      exit 1
    fi
  done
  [ -r "$CA_RAIZ" ] || { log "falta la CA raíz de Amazon en $CA_RAIZ: reconstruye la imagen con ./fleet/build.sh"; exit 1; }
  IOT_DATA_ENDPOINT="$(sed -n 's/^IOT_DATA_ENDPOINT=//p' "$ID_DIR/endpoints.env")"
  IOT_CRED_ENDPOINT="$(sed -n 's/^IOT_CRED_ENDPOINT=//p' "$ID_DIR/endpoints.env")"
  if [ -z "$IOT_DATA_ENDPOINT" ] || [ -z "$IOT_CRED_ENDPOINT" ]; then log "endpoints.env no trae los dos endpoints"; exit 1; fi

  mkdir -p "$ROOT"
  install -m 644 "$ID_DIR/device.pem.crt" "$ROOT/device.pem.crt"
  install -m 600 "$ID_DIR/private.pem.key" "$ROOT/private.pem.key"
  install -m 644 "$CA_RAIZ" "$ROOT/AmazonRootCA1.pem"
  # el nucleus decide el formato por la extensión: sin .yaml no lo lee
  local tmp cfg; tmp="$(mktemp -d)"; cfg="$tmp/config.yaml"
  cat > "$cfg" <<CFG
---
system:
  certificateFilePath: "$ROOT/device.pem.crt"
  privateKeyPath: "$ROOT/private.pem.key"
  rootCaPath: "$ROOT/AmazonRootCA1.pem"
  rootpath: "$ROOT"
  thingName: "$THING_NAME"
services:
  aws.greengrass.Nucleus:
    componentType: "NUCLEUS"
    version: "${GREENGRASS_VERSION:?falta GREENGRASS_VERSION}"
    configuration:
      awsRegion: "$AWS_REGION"
      iotRoleAlias: "${TES_ROLE_ALIAS_NAME:-GreengrassCoreTokenExchangeRoleAlias}"
      iotDataEndpoint: "$IOT_DATA_ENDPOINT"
      iotCredEndpoint: "$IOT_CRED_ENDPOINT"
CFG
  log "primer arranque: $THING_NAME con la identidad de Terraform ($AWS_REGION)"
  java -Droot="$ROOT" -Dlog.store=FILE \
    -jar "$INSTALADOR" \
    --init-config "$cfg" \
    --component-default-user "${COMPONENT_DEFAULT_USER:-ggc_user:ggc_group}" \
    --setup-system-service false \
    --start false
  rm -rf "$tmp"
}

if [ ! -f "$MARCA" ]; then
  case "$IDENTIDAD" in
    terraform)  ( instalar_con_identidad ) ;;
    instalador) ( aprovisionar ) ;;
    *) log "IDENTIDAD=$IDENTIDAD no existe: usa instalador o terraform"; exit 1 ;;
  esac
  date -u +%Y-%m-%dT%H:%M:%SZ > "$MARCA"
  log "aprovisionada"
fi

[ -x "$LOADER" ] || { log "no encuentro $LOADER: la instalación no terminó bien"; exit 1; }

log "arrancando el nucleus de ${THING_NAME:-esta bomba}"
exec /bin/sh "$LOADER"
