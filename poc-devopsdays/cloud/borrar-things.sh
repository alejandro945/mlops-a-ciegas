#!/usr/bin/env bash
# Borra de AWS las cosas (things) de la flota, sus certificados y sus core devices.
#   ./cloud/borrar-things.sh bomba-01 bomba-02 …
# Lo usan ./fleet/down.sh --borrar-things y ./cloud/teardown.sh. No toca las políticas ni los thing groups.
set -euo pipefail
REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
[ "$#" -gt 0 ] || { echo "uso: $0 bomba-01 [bomba-02 …]"; exit 1; }

for t in "$@"; do
  echo "▶ borrando $t de AWS"
  principales="$(aws iot list-thing-principals --thing-name "$t" --query 'principals[]' --output text 2>/dev/null || true)"
  for p in $principales; do
    aws iot detach-thing-principal --thing-name "$t" --principal "$p" >/dev/null
    for pol in $(aws iot list-attached-policies --target "$p" --query 'policies[].policyName' --output text); do
      aws iot detach-policy --policy-name "$pol" --target "$p"
    done
    cert="${p##*/}"
    aws iot update-certificate --certificate-id "$cert" --new-status INACTIVE
    aws iot delete-certificate --certificate-id "$cert"
  done
  aws greengrassv2 delete-core-device --core-device-thing-name "$t" 2>/dev/null || true
  aws iot delete-thing --thing-name "$t" 2>/dev/null || true
done
echo "✔ listo"
