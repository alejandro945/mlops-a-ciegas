#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Uploads the PoC (code + build/ + fleet audio) to the bucket, so the EC2 can pull it with `fetch-poc`.
#  Runs on your laptop, from any folder, after `terraform apply`.
#
#  Usage:  ./infra/upload-to-host.sh            (reads the bucket from the Terraform outputs)
#          BUCKET=station-123-us-east-1 ./infra/upload-to-host.sh
#
#  Does not upload the MIMII DUE zip or the synthetic set: only data/station/ (built by model/prepare_data.py).
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="${BUCKET:-$(terraform -chdir=infra output -raw bucket)}"
[ -n "$BUCKET" ] || { echo "no bucket to upload to: run terraform apply or pass BUCKET="; exit 1; }
[ -d data/station ] || { echo "data/station is missing: run python3 model/prepare_data.py --data data/dev_data_pump.zip"; exit 1; }

aws s3 sync . "s3://$BUCKET/repo/" --delete \
  --exclude 'data/*' --exclude '*.zip' --exclude '*/__pycache__/*' --exclude '*.pyc' --exclude '.DS_Store' \
  --exclude 'infra/*' --exclude 'fleet/logs/*' --exclude 'fleet/.bootstrap/*' --exclude 'tests/*'
aws s3 sync data/station "s3://$BUCKET/repo/data/station/" --delete --exclude '.DS_Store'
echo "▶ uploaded to s3://$BUCKET/repo/   ·   on the EC2: fetch-poc"
