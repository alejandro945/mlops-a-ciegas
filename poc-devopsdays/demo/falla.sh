#!/usr/bin/env bash
# La bomba suena con falla (o vuelve a sonar normal). Corre en el equipo que tiene Docker.
#   ./demo/falla.sh bomba-03        la 3 suena como la bomba B del inicio de la charla
#   ./demo/falla.sh bomba-03 off    vuelve a normal
# Por dentro: escribe "falla" o "normal" en /run/estacion/modo; el componente lo relee en cada clip.
set -euo pipefail
B="${1:?bomba (bomba-01 … bomba-05)}"
case "${2:-on}" in
  on)  MODO=falla ;;
  off) MODO=normal ;;
  *) echo "uso: $0 <bomba> [on|off]"; exit 1 ;;
esac
[[ "$B" =~ ^bomba-0[1-5]$ ]] || { echo "bomba desconocida: $B  (bomba-01 … bomba-05)"; exit 1; }

docker exec "$B" sh -c 'echo "$1" > /run/estacion/modo' _ "$MODO"
echo "▶ $B suena: $MODO  $(date +%H:%M:%S)"
