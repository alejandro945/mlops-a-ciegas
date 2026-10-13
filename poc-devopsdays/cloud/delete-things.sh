#!/usr/bin/env bash
# Deletes the fleet's things from AWS, along with their certificates and core devices.
#   ./cloud/delete-things.sh pump-01 pump-02 …
# Used by ./fleet/down.sh --delete-things and ./cloud/teardown.sh. Leaves policies and thing groups alone.
set -euo pipefail
REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
[ "$#" -gt 0 ] || { echo "usage: $0 pump-01 [pump-02 …]"; exit 1; }

for t in "$@"; do
  echo "▶ deleting $t from AWS"
  principals="$(aws iot list-thing-principals --thing-name "$t" --query 'principals[]' --output text 2>/dev/null || true)"
  for p in $principals; do
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
echo "✔ done"
