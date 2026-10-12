#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Sube la PoC (código + build/ + audio de la flota) al bucket, para que la EC2 la baje con `traer-poc`.
#  Corre en tu laptop, desde cualquier carpeta, después de `terraform apply`.
#
#  Uso:  ./infra/subir-al-host.sh            (lee el bucket de las salidas de Terraform)
#        BUCKET=estacion-123-us-east-1 ./infra/subir-al-host.sh
#
#  No sube el zip de MIMII DUE ni el set sintético: solo data/estacion/ (lo que arma model/prepare_data.py).
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="${BUCKET:-$(terraform -chdir=infra output -raw bucket)}"
[ -n "$BUCKET" ] || { echo "no sé a qué bucket subir: corre terraform apply o pasa BUCKET="; exit 1; }
[ -d data/estacion ] || { echo "falta data/estacion: corre python3 model/prepare_data.py --data data/dev_data_pump.zip"; exit 1; }

aws s3 sync . "s3://$BUCKET/repo/" --delete \
  --exclude 'data/*' --exclude '*.zip' --exclude '*/__pycache__/*' --exclude '*.pyc' --exclude '.DS_Store' \
  --exclude 'infra/*' --exclude 'fleet/logs/*' --exclude 'fleet/.bootstrap/*' --exclude 'tests/*'
aws s3 sync data/estacion "s3://$BUCKET/repo/data/estacion/" --delete --exclude '.DS_Store'
echo "▶ subido a s3://$BUCKET/repo/   ·   en la EC2: traer-poc"
