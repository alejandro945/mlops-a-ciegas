#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Before `terraform destroy`: deletes what Greengrass created on its own and Terraform does not
#  know about, the core devices (each pump registers one the first time it connects).
#  Things, certificates, rings and everything else are deleted by terraform destroy.
#
#  Usage:  ./infra/clean-core-devices.sh            (from your laptop or from the EC2)
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"

DEVICES="$(aws greengrassv2 list-core-devices \
  --query "coreDevices[?starts_with(coreDeviceThingName, 'pump-')].coreDeviceThingName" --output text)"
for d in $DEVICES; do
  [ "$d" = None ] && continue
  aws greengrassv2 delete-core-device --core-device-thing-name "$d"
  echo "▶ core device $d deleted"
done
echo "✔ done. Next: terraform -chdir=infra destroy"
