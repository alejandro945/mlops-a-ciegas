#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Pump entrypoint (image station/greengrass)
#
#  First boot : IDENTITY=installer (default) → provisions the pump
#               (thing, thing group, token exchange role) with temporary
#               credentials mounted at /run/aws-bootstrap/credentials.
#               IDENTITY=terraform → the pump already exists in AWS (infra/):
#               installs the nucleus with the certificate mounted at
#               /run/station-id, without any AWS credentials.
#  Later boots: no credentials; the identity already lives in the volume
#               /greengrass/v2 and only the nucleus starts.
#
#  The nucleus stays in the foreground (PID 1 under docker --init).
#  Variables: THING_NAME, THING_GROUP_NAME, AWS_REGION, THING_POLICY_NAME,
#             TES_ROLE_NAME, TES_ROLE_ALIAS_NAME, COMPONENT_DEFAULT_USER,
#             IDENTITY (installer|terraform), ID_DIR, ROOT_CA, STATION_RUN_DIR, GREENGRASS_VERSION.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="${GGC_ROOT_PATH:-/greengrass/v2}"
MARKER="$ROOT/.station-provisioned"
LOADER="$ROOT/alts/current/distro/bin/loader"
CREDS="${CREDS_FILE:-/run/aws-bootstrap/credentials}"
INSTALLER="${INSTALLER_JAR:-/opt/greengrass-installer/lib/Greengrass.jar}"
MODE_DIR="${STATION_RUN_DIR:-/run/station}"
ID_DIR="${ID_DIR:-/run/station-id}"
ROOT_CA="${ROOT_CA:-/opt/greengrass-installer/AmazonRootCA1.pem}"
IDENTITY="${IDENTITY:-installer}"
log() { echo "[station] $*"; }

# What the pump "hears": the demo writes this file with docker exec (as root);
# the component re-reads it on every clip. It survives a container restart.
mkdir -p "$MODE_DIR"
[ -f "$MODE_DIR/mode" ] || echo normal > "$MODE_DIR/mode"
chmod 755 "$MODE_DIR"
chmod 644 "$MODE_DIR/mode"

# For debugging:  docker run --rm -it station/greengrass bash
if [ "$#" -gt 0 ]; then exec "$@"; fi

provision() {
  : "${THING_NAME:?THING_NAME is missing}"
  : "${THING_GROUP_NAME:?THING_GROUP_NAME is missing}"
  : "${AWS_REGION:?AWS_REGION is missing}"
  if [ ! -r "$CREDS" ]; then
    log "this pump has no identity and there are no credentials in $CREDS."
    log "start it with ./fleet/up.sh (it mounts the temporary credentials)."
    exit 1
  fi

  # The credentials live only in this subprocess: the nucleus starts without them.
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
  [ -n "${AWS_ACCESS_KEY_ID:-}" ] || { log "could not read the credentials from $CREDS"; exit 1; }

  log "first boot: provisioning $THING_NAME in $THING_GROUP_NAME ($AWS_REGION)"
  java -Droot="$ROOT" -Dlog.store=FILE \
    -jar "$INSTALLER" \
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

# The pump already exists in AWS (Terraform created the thing, certificate, policy and ring):
# only the nucleus is installed with that certificate. No AWS credentials enter the container.
install_with_identity() {
  : "${THING_NAME:?THING_NAME is missing}"
  : "${AWS_REGION:?AWS_REGION is missing}"
  local f
  for f in device.pem.crt private.pem.key endpoints.env; do
    if [ ! -r "$ID_DIR/$f" ]; then
      log "$ID_DIR/$f is missing: this pump does not have its identity mounted."
      log "start it with IDENTITY=terraform ./fleet/up.sh (it fetches it from Parameter Store)."
      exit 1
    fi
  done
  [ -r "$ROOT_CA" ] || { log "the Amazon root CA is missing at $ROOT_CA: rebuild the image with ./fleet/build.sh"; exit 1; }
  IOT_DATA_ENDPOINT="$(sed -n 's/^IOT_DATA_ENDPOINT=//p' "$ID_DIR/endpoints.env")"
  IOT_CRED_ENDPOINT="$(sed -n 's/^IOT_CRED_ENDPOINT=//p' "$ID_DIR/endpoints.env")"
  if [ -z "$IOT_DATA_ENDPOINT" ] || [ -z "$IOT_CRED_ENDPOINT" ]; then log "endpoints.env does not have both endpoints"; exit 1; fi

  mkdir -p "$ROOT"
  install -m 644 "$ID_DIR/device.pem.crt" "$ROOT/device.pem.crt"
  install -m 600 "$ID_DIR/private.pem.key" "$ROOT/private.pem.key"
  install -m 644 "$ROOT_CA" "$ROOT/AmazonRootCA1.pem"
  # the nucleus picks the format by the extension: without .yaml it does not read it
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
    version: "${GREENGRASS_VERSION:?GREENGRASS_VERSION is missing}"
    configuration:
      awsRegion: "$AWS_REGION"
      iotRoleAlias: "${TES_ROLE_ALIAS_NAME:-GreengrassCoreTokenExchangeRoleAlias}"
      iotDataEndpoint: "$IOT_DATA_ENDPOINT"
      iotCredEndpoint: "$IOT_CRED_ENDPOINT"
CFG
  log "first boot: $THING_NAME with the Terraform identity ($AWS_REGION)"
  java -Droot="$ROOT" -Dlog.store=FILE \
    -jar "$INSTALLER" \
    --init-config "$cfg" \
    --component-default-user "${COMPONENT_DEFAULT_USER:-ggc_user:ggc_group}" \
    --setup-system-service false \
    --start false
  rm -rf "$tmp"
}

if [ ! -f "$MARKER" ]; then
  case "$IDENTITY" in
    terraform) ( install_with_identity ) ;;
    installer) ( provision ) ;;
    *) log "IDENTITY=$IDENTITY does not exist: use installer or terraform"; exit 1 ;;
  esac
  date -u +%Y-%m-%dT%H:%M:%SZ > "$MARKER"
  log "provisioned"
fi

[ -x "$LOADER" ] || { log "cannot find $LOADER: the installation did not finish properly"; exit 1; }

log "starting the nucleus of ${THING_NAME:-this pump}"
exec /bin/sh "$LOADER"
