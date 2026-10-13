#!/usr/bin/env bash
# Builds the pump image:  station/greengrass
#   ./fleet/build.sh
#   GREENGRASS_VERSION=2.18.3 GREENGRASS_SHA256=<hash> ./fleet/build.sh
set -euo pipefail
cd "$(dirname "$0")"

VERSION="${GREENGRASS_VERSION:-2.18.3}"
BASE="${BASE_IMAGE:-debian:12-slim}"

[ "$(uname -s)" = "Linux" ] || echo "warning: AWS requires a Linux host for Greengrass in Docker (this one is $(uname -s))."

echo "▶ building station/greengrass:$VERSION (nucleus $VERSION on $BASE)"
docker build \
  --build-arg "GREENGRASS_VERSION=$VERSION" \
  --build-arg "GREENGRASS_SHA256=${GREENGRASS_SHA256:-}" \
  --build-arg "BASE_IMAGE=$BASE" \
  -t "station/greengrass:$VERSION" -t "station/greengrass:latest" .

echo "✔ image ready: station/greengrass:$VERSION"
echo "  (the hash of the nucleus zip is in the build log; keep it in GREENGRASS_SHA256)"
