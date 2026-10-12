#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Antes de `terraform destroy`: borra lo que Greengrass creó solo y Terraform no conoce,
#  los core devices (se registran cuando cada bomba se conecta por primera vez).
#  Los things, certificados, anillos y todo lo demás los borra terraform destroy.
#
#  Uso:  ./infra/limpiar-core-devices.sh            (desde tu laptop o desde la EC2)
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"

for b in bomba-01 bomba-02 bomba-03 bomba-04 bomba-05; do
  if aws greengrassv2 get-core-device --core-device-thing-name "$b" >/dev/null 2>&1; then
    aws greengrassv2 delete-core-device --core-device-thing-name "$b"
    echo "▶ core device $b borrado"
  fi
done
echo "✔ listo. Siguiente: terraform -chdir=infra destroy"
