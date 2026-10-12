#!/usr/bin/env bash
# Lo que se ve en pantalla durante la demo: las bombas contando cada decisión.
#   bomba-03  v1.0.0  ALERTA  score 0,82 (umbral 0,50)  entrada 1,1  4 ms  · llegó 40 s tarde
#
#   ./demo/watch.sh               todas las bombas
#   ./demo/watch.sh bomba-03      solo una
#   DESDE=10m ./demo/watch.sh     empieza con los últimos 10 minutos (por defecto, 1)
set -euo pipefail
REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
AQUI="$(cd "$(dirname "$0")" && pwd)"

aws logs tail /estacion/eventos --follow --format short --since "${DESDE:-1m}" \
  | python3 -u "$AQUI/formato_eventos.py" ${1:+"$1"}
