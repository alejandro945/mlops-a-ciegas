#!/usr/bin/env bash
# La bomba cambia de velocidad (el dominio nuevo del dataset). Ningún error: los scores se corren.
#   ./demo/dominio.sh bomba-05 nuevo       otra velocidad y otro ruido de ambiente
#   ./demo/dominio.sh bomba-05 normal      vuelve a como sonaba
# Por dentro: escribe "nuevo" o "normal" en /run/estacion/modo.
set -euo pipefail
B="${1:?bomba (bomba-01 … bomba-05)}"
MODO="${2:?nuevo | normal}"
case "$MODO" in nuevo|normal) ;; *) echo "uso: $0 <bomba> <nuevo|normal>"; exit 1 ;; esac
[[ "$B" =~ ^bomba-0[1-5]$ ]] || { echo "bomba desconocida: $B  (bomba-01 … bomba-05)"; exit 1; }

docker exec "$B" sh -c 'echo "$1" > /run/estacion/modo' _ "$MODO"
echo "▶ $B suena: $MODO  $(date +%H:%M:%S)"
