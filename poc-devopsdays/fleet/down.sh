#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  PoC · La estación · apagar la flota
#
#  Uso:  ./fleet/down.sh                   detiene y borra los contenedores y la red;
#                                          conserva los volúmenes (la identidad de cada bomba)
#        ./fleet/down.sh --borrar-things   además borra los volúmenes y, en AWS, los
#                                          things, sus certificados y los core devices
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

BOMBAS=(bomba-01 bomba-02 bomba-03 bomba-04 bomba-05)
BORRAR=0
for a in "$@"; do
  case "$a" in
    --borrar-things) BORRAR=1 ;;
    -h|--help) awk 'NR>1 && /^#/ {print} /^set -/ {exit}' "$0"; exit 0 ;;
    *) echo "opción desconocida: $a  (usa --borrar-things)"; exit 1 ;;
  esac
done

for b in "${BOMBAS[@]}"; do
  if docker inspect "$b" >/dev/null 2>&1; then
    docker stop -t 30 "$b" >/dev/null 2>&1 || true     # SIGTERM: el nucleus se apaga solo
    docker rm -f "$b" >/dev/null
    echo "▶ $b apagada"
  fi
done
docker network rm estacion >/dev/null 2>&1 && echo "▶ red estacion borrada" || true
rm -f fleet/.bootstrap/credentials

if [ "$BORRAR" = 1 ] && [ "${IDENTIDAD:-instalador}" = terraform ]; then
  echo "✘ con IDENTIDAD=terraform, las cosas y los certificados los maneja Terraform:"
  echo "   ./infra/limpiar-core-devices.sh && terraform -chdir=infra destroy"
  exit 1
fi
if [ "$BORRAR" = 1 ]; then
  for b in "${BOMBAS[@]}"; do
    docker volume rm "$b-gg" >/dev/null 2>&1 && echo "▶ volumen $b-gg borrado" || true
  done
  ./cloud/borrar-things.sh "${BOMBAS[@]}"
  echo "✔ flota borrada de este equipo y de AWS (los thing groups siguen: los borra cloud/teardown.sh)"
else
  echo "✔ flota apagada. Los volúmenes conservan la identidad: ./fleet/up.sh las reconecta sin credenciales."
fi
