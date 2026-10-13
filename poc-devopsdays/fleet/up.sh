#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  PoC · The station · bring up the fleet
#
#  Network "station" + five containers with the real Greengrass nucleus.
#    pump-01        → thing group StationRing0 (canary)
#    pump-02 … 05   → thing group StationRing1
#
#  Usage:  ./fleet/up.sh                 the five pumps
#          ./fleet/up.sh --small         each pump limited to a "small device"
#          ./fleet/up.sh --recreate      recreates the containers (keeps the identity)
#          REGION=us-east-1 CPUS=2 MEM=2g NUCLEUS_HEAP=192m ./fleet/up.sh
#          DATA=<folder>    where the audio comes from (default data/station, from model/prepare_data.py)
#
#  First boot, two paths:
#    IDENTITY=terraform ./fleet/up.sh   the pumps already exist in AWS (infra/, terraform apply):
#        fetches each one's certificate from Parameter Store, mounts it only during the
#        installation and deletes it from disk. No AWS credentials enter the containers.
#    ./fleet/up.sh  (IDENTITY=installer)   the Greengrass installer registers each pump
#        with TEMPORARY credentials from your AWS CLI session, deleted when it finishes.
#  Later boots: no credentials; each pump's identity lives in its volume <pump>-gg.
#  Requires: docker (Linux host), aws cli v2, python3, ./fleet/build.sh, and terraform apply or cloud/setup.sh.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="${REGION:-us-east-1}"
IMAGE="${IMAGE:-station/greengrass:latest}"
NETWORK="station"
DATA="${DATA:-data/station}"
case "$DATA" in /*) ;; *) DATA="$PWD/$DATA" ;; esac
LOGS="$PWD/fleet/logs"
BOOT="$PWD/fleet/.bootstrap"
THING_POLICY="${THING_POLICY_NAME:-StationThingPolicy}"
NUCLEUS_HEAP="${NUCLEUS_HEAP-256m}"       # heap cap for each nucleus (each one is a JVM); empty = no cap
WAIT_SECONDS="${WAIT_SECONDS:-300}"      # maximum seconds to provision one pump
CPUS="${CPUS:-}"; MEM="${MEM:-}"
IDENTITY="${IDENTITY:-installer}"        # installer | terraform
case "$IDENTITY" in installer|terraform) ;; *) echo "IDENTITY=$IDENTITY does not exist: use installer or terraform"; exit 1 ;; esac
PUMPS=(pump-01 pump-02 pump-03 pump-04 pump-05)

SMALL=0; RECREATE=0
for a in "$@"; do
  case "$a" in
    --small) SMALL=1 ;;
    --recreate) RECREATE=1 ;;
    -h|--help) awk 'NR>1 && /^#/ {print} /^set -/ {exit}' "$0"; exit 0 ;;
    *) echo "unknown option: $a  (use --small, --recreate)"; exit 1 ;;
  esac
done
if [ "$SMALL" = 1 ]; then CPUS="${CPUS:-1}"; MEM="${MEM:-1g}"; fi

group_of() { if [ "$1" = "pump-01" ]; then echo StationRing0; else echo StationRing1; fi; }

[ "$(uname -s)" = "Linux" ] || echo "warning: AWS requires a Linux host for Greengrass in Docker (this one is $(uname -s))."
docker image inspect "$IMAGE" >/dev/null 2>&1 || { echo "image $IMAGE is missing: run ./fleet/build.sh"; exit 1; }
for p in "${PUMPS[@]}"; do
  [ -d "$DATA/$p" ] || { echo "the audio for $p is missing in $DATA/$p"
                         echo "generate the data with model/prepare_data.py (or point DATA= to another folder)"; exit 1; }
  # the component runs as ggc_user, not root: the audio must be world-readable
  chmod -R a+rX "$DATA/$p" 2>/dev/null || echo "warning: could not open read permissions on $DATA/$p"
done

# does the pump's volume already have an identity (thing, certificate, nucleus installed)?
provisioned() {
  docker volume inspect "$1-gg" >/dev/null 2>&1 &&
  docker run --rm --entrypoint test -v "$1-gg:/greengrass/v2:ro" "$IMAGE" -f /greengrass/v2/.station-provisioned
}

# Temporary credentials from your session -> file in ~/.aws/credentials format
write_credentials() {
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
    sys.exit("no AWS credentials found (neither aws configure export-credentials nor AWS_* variables)")
if not st:
    print("warning: these are long-lived credentials; better use a role with a temporary session.", file=sys.stderr)
cp = configparser.ConfigParser(interpolation=None)
cp["default"] = {"aws_access_key_id": ak, "aws_secret_access_key": sk}
if st:
    cp["default"]["aws_session_token"] = st
cp.write(sys.stdout)
PY
  )
}
# The identity Terraform created (certificate, key, endpoints) -> $BOOT/<pump>/, only for the installation
write_identity() {   # $1 = pump
  local p="$1" d="$BOOT/$1"
  # if a previous attempt was left restarting, Docker recreated $d as root when mounting it
  rm -rf "$d"; mkdir -p "$d"; chmod 700 "$d"
  param() { aws ssm get-parameter --region "$REGION" --name "$1" --with-decryption --query Parameter.Value --output text; }
  ( umask 077
    param "/station/pumps/$p/cert" > "$d/device.pem.crt"
    param "/station/pumps/$p/key"  > "$d/private.pem.key"
    printf 'IOT_DATA_ENDPOINT=%s\nIOT_CRED_ENDPOINT=%s\n' \
      "$(param /station/iot/data_endpoint)" "$(param /station/iot/cred_endpoint)" > "$d/endpoints.env" )
  if ! grep -q "BEGIN CERTIFICATE" "$d/device.pem.crt" || ! grep -q "PRIVATE KEY" "$d/private.pem.key"; then
    echo "✘ could not find the identity of $p in Parameter Store (/station/pumps/$p): did you run terraform apply in infra/?"
    rm -rf "$d"; return 1
  fi
}
trap 'rm -f "$BOOT/credentials"; rm -rf "$BOOT"/pump-*' EXIT

create() {   # $1 = pump · $2 = "with-identity" on first boot with IDENTITY=terraform
  local p="$1" g; g="$(group_of "$p")"
  mkdir -p "$LOGS/$p" "$BOOT"; chmod 700 "$BOOT"
  local args=(run -d --name "$p" --hostname "$p" --init --restart unless-stopped --network "$NETWORK"
    --log-driver json-file --log-opt max-size=10m --log-opt max-file=3
    -v "$p-gg:/greengrass/v2"                    # identity and nucleus state
    -v "$LOGS/$p:/greengrass/v2/logs"            # nucleus and component logs, on the host
    -v "$DATA/$p:/data/station/$p:ro"            # the pump's audio, read-only
    -v "$BOOT:/run/aws-bootstrap:ro"             # empty except during the first boot
    -e "AWS_REGION=$REGION" -e "THING_NAME=$p" -e "THING_GROUP_NAME=$g"
    -e "THING_POLICY_NAME=$THING_POLICY")
  if [ "$IDENTITY" = terraform ]; then args+=(-e "IDENTITY=terraform"); fi
  if [ "${2:-}" = with-identity ]; then args+=(-v "$BOOT/$p:/run/station-id:ro"); fi
  if [ -n "$NUCLEUS_HEAP" ]; then args+=(-e "JAVA_TOOL_OPTIONS=-Xmx${NUCLEUS_HEAP} -XX:+UseSerialGC"); fi
  if [ -n "$CPUS" ]; then args+=(--cpus "$CPUS"); fi
  if [ -n "$MEM" ];  then args+=(--memory "$MEM" --memory-swap "$MEM"); fi
  docker "${args[@]}" "$IMAGE" >/dev/null
}

wait_provisioned() {   # $1 = pump
  local p="$1" i
  for ((i = 0; i < WAIT_SECONDS; i += 2)); do
    if docker exec "$p" test -f /greengrass/v2/.station-provisioned 2>/dev/null; then return 0; fi
    if [ "$(docker inspect -f '{{.State.Running}}' "$p" 2>/dev/null || echo false)" != "true" ]; then
      echo "✘ $p stopped before finishing:"; docker logs --tail 40 "$p" 2>&1 || true; return 1
    fi
    sleep 2
  done
  echo "✘ $p did not finish provisioning in ${WAIT_SECONDS} s:"; docker logs --tail 40 "$p" 2>&1 || true
  return 1
}

# ── 1 · network ──────────────────────────────────────────────────────
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK" >/dev/null
echo "▶ network $NETWORK ready"

# ── 2 · sort out which pumps already exist and which need an identity ─
PENDING=()
for p in "${PUMPS[@]}"; do
  if [ "$RECREATE" = 1 ] && docker inspect "$p" >/dev/null 2>&1; then docker rm -f "$p" >/dev/null; fi
  if ! provisioned "$p"; then
    docker rm -f "$p" >/dev/null 2>&1 || true
    PENDING+=("$p"); continue
  fi
  state="$(docker inspect -f '{{.State.Status}}' "$p" 2>/dev/null || true)"
  case "$state" in
    running) echo "▶ $p already running" ;;
    "")      create "$p"; echo "▶ $p created (with its identity, no credentials)" ;;
    *)       docker start "$p" >/dev/null; echo "▶ $p started" ;;
  esac
done

# ── 3 · first boot: provision one at a time ──────────────────────────
if [ "${#PENDING[@]}" -gt 0 ] && [ "$IDENTITY" = terraform ]; then
  echo "▶ installing ${PENDING[*]} with the Terraform identity (no AWS credentials in the containers)"
  for p in "${PENDING[@]}"; do
    write_identity "$p" || exit 1
    create "$p" with-identity
    wait_provisioned "$p" || exit 1
    rm -rf "${BOOT:?}/$p"
    echo "✔ $p installed in $(group_of "$p")"
  done
elif [ "${#PENDING[@]}" -gt 0 ]; then
  echo "▶ provisioning ${PENDING[*]} (temporary credentials; deleted when done)"
  write_credentials
  for p in "${PENDING[@]}"; do
    create "$p"
    wait_provisioned "$p" || exit 1
    echo "✔ $p provisioned in $(group_of "$p")"
  done
  rm -f "$BOOT/credentials"
fi

# ── 4 · summary ──────────────────────────────────────────────────────
echo
docker ps --filter "name=pump-" --format 'table {{.Names}}\t{{.Status}}'
cat <<EOF2

✔ Fleet up. Each pump takes a couple of minutes to show up as Healthy.
  aws greengrassv2 list-core-devices --region $REGION --query 'coreDevices[].[coreDeviceThingName,status]' --output table
  one pump's logs:  tail -f fleet/logs/pump-03/greengrass.log
Next: ./demo/publish.sh 1.0.0   and   ./demo/deploy.sh 1.0.0 all
EOF2
