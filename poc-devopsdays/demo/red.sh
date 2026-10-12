#!/usr/bin/env bash
# Corta y devuelve la red de UNA bomba (la saca de la red Docker "estacion").
#   ./demo/red.sh off bomba-03   la 3 sigue escuchando; sus eventos quedan en la cola del nucleus
#   ./demo/red.sh on  bomba-03   vuelve la red; los eventos guardados llegan a la nube
set -euo pipefail
ESTADO="${1:?off | on}"
B="${2:?bomba (bomba-01 … bomba-05)}"
[[ "$B" =~ ^bomba-0[1-5]$ ]] || { echo "bomba desconocida: $B  (bomba-01 … bomba-05)"; exit 1; }

case "$ESTADO" in
  off) docker network disconnect estacion "$B"
       echo "▶ $B sin red  $(date +%H:%M:%S)" ;;
  on)  docker network connect estacion "$B"
       echo "▶ $B con red de vuelta  $(date +%H:%M:%S)" ;;
  *)   echo "uso: $0 <off|on> <bomba>"; exit 1 ;;
esac
