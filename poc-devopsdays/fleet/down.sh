#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  PoC · The station · shut down the fleet
#
#  Usage:  ./fleet/down.sh                   stops and removes the containers and the network;
#                                            keeps the volumes (each pump's identity)
#          ./fleet/down.sh --delete-things   also removes the volumes and, in AWS, the
#                                            things, their certificates and the core devices
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

PUMPS=(pump-01 pump-02 pump-03 pump-04 pump-05)
DELETE=0
for a in "$@"; do
  case "$a" in
    --delete-things) DELETE=1 ;;
    -h|--help) awk 'NR>1 && /^#/ {print} /^set -/ {exit}' "$0"; exit 0 ;;
    *) echo "unknown option: $a  (use --delete-things)"; exit 1 ;;
  esac
done

for p in "${PUMPS[@]}"; do
  if docker inspect "$p" >/dev/null 2>&1; then
    docker stop -t 30 "$p" >/dev/null 2>&1 || true     # SIGTERM: the nucleus shuts itself down
    docker rm -f "$p" >/dev/null
    echo "▶ $p stopped"
  fi
done
docker network rm station >/dev/null 2>&1 && echo "▶ network station removed" || true
rm -f fleet/.bootstrap/credentials

if [ "$DELETE" = 1 ] && [ "${IDENTITY:-installer}" = terraform ]; then
  echo "✘ with IDENTITY=terraform, the things and certificates are managed by Terraform:"
  echo "   ./infra/clean-core-devices.sh && terraform -chdir=infra destroy"
  exit 1
fi
if [ "$DELETE" = 1 ]; then
  for p in "${PUMPS[@]}"; do
    docker volume rm "$p-gg" >/dev/null 2>&1 && echo "▶ volume $p-gg removed" || true
  done
  ./cloud/delete-things.sh "${PUMPS[@]}"
  echo "✔ fleet deleted from this machine and from AWS (the thing groups remain: cloud/teardown.sh deletes them)"
else
  echo "✔ fleet stopped. The volumes keep the identity: ./fleet/up.sh reconnects them without credentials."
fi
