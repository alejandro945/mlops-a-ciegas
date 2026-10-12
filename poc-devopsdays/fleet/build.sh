#!/usr/bin/env bash
# Construye la imagen de la bomba:  estacion/greengrass
#   ./fleet/build.sh
#   GREENGRASS_VERSION=2.18.3 GREENGRASS_SHA256=<hash> ./fleet/build.sh
set -euo pipefail
cd "$(dirname "$0")"

VERSION="${GREENGRASS_VERSION:-2.18.3}"
BASE="${BASE_IMAGE:-debian:12-slim}"

[ "$(uname -s)" = "Linux" ] || echo "aviso: AWS pide un host Linux para Greengrass en Docker (este es $(uname -s))."

echo "▶ construyendo estacion/greengrass:$VERSION (nucleus $VERSION sobre $BASE)"
docker build \
  --build-arg "GREENGRASS_VERSION=$VERSION" \
  --build-arg "GREENGRASS_SHA256=${GREENGRASS_SHA256:-}" \
  --build-arg "BASE_IMAGE=$BASE" \
  -t "estacion/greengrass:$VERSION" -t "estacion/greengrass:latest" .

echo "✔ imagen lista: estacion/greengrass:$VERSION"
echo "  (el hash del zip del nucleus salió en el log del build; guárdalo en GREENGRASS_SHA256)"
