#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Publishes a model version as a version of the component com.station.Listener
#    1. uploads build/<version>/{inference.py,features.py,model.onnx,stats.json}
#       to s3://station-<account>-<region>/station/<version>/
#    2. creates the component version from the recipe, with the threshold from stats.json
#
#  Usage:  ./demo/publish.sh 1.0.0
#          ./demo/publish.sh 1.0.0 --allow-synthetic     (only to test the pipeline)
#
#  A published version is never touched: Greengrass computes each artifact's digest when
#  creating it. To change anything, upload a new version.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."

V="${1:?version (for example 1.0.0)}"; shift || true
ALLOW_SYNTHETIC=0
for a in "$@"; do
  case "$a" in
    --allow-synthetic) ALLOW_SYNTHETIC=1 ;;
    *) echo "unknown option: $a  (use --allow-synthetic)"; exit 1 ;;
  esac
done
[[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "the version must look like 1.0.0 (got: $V)"; exit 1; }

REGION="${REGION:-us-east-1}"; export AWS_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${BUCKET:-station-${ACCOUNT}-${REGION}}"
COMPONENT="com.station.Listener"
SRC="build/$V"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

for f in inference.py features.py model.onnx stats.json; do
  [ -f "$SRC/$f" ] || { echo "$SRC/$f is missing  (train with model/train.py; see model/README.md)"; exit 1; }
done

# threshold, synthetic?, and that stats.json belongs to this model and this version
INFO="$(python3 - "$SRC" "$V" <<'PY'
import hashlib, json, sys
src, v = sys.argv[1:3]
st = json.load(open(f"{src}/stats.json"))
if "threshold" not in st:
    sys.exit("stats.json has no threshold field")
if st.get("version") not in (None, v):
    sys.exit(f"stats.json is for version {st['version']}, not {v}")
sha = hashlib.sha256(open(f"{src}/model.onnx", "rb").read()).hexdigest()
if st.get("sha256") not in (None, sha):
    sys.exit("the sha256 in stats.json is not model.onnx's: retrain or copy the complete files")
print(st["threshold"], 1 if st.get("synthetic") else 0)
PY
)"
THRESHOLD="${INFO% *}"; SYNTHETIC="${INFO##* }"

if [ "$SYNTHETIC" = "1" ] && [ "$ALLOW_SYNTHETIC" != "1" ]; then
  echo "✘ $SRC/stats.json says \"synthetic\": true. That model learned from synthetic audio:"
  echo "  it is good for testing the pipeline, not for showing numbers. If that is what you want: --allow-synthetic"
  exit 1
fi
[ "$SYNTHETIC" = "1" ] && echo "warning: synthetic model (--allow-synthetic). No number from this run goes on a slide."

aws s3api head-bucket --bucket "$BUCKET" >/dev/null 2>&1 || { echo "s3://$BUCKET does not exist: run ./cloud/setup.sh"; exit 1; }

ARN="arn:aws:greengrass:$REGION:$ACCOUNT:components:$COMPONENT:versions:$V"
if aws greengrassv2 describe-component --arn "$ARN" >/dev/null 2>&1; then
  echo "▶ $COMPONENT $V is already published: leaving it alone (artifacts are immutable)."
  echo "  To change anything, upload a new version."
  exit 0
fi

echo "▶ uploading $SRC to s3://$BUCKET/station/$V/"
for f in inference.py features.py model.onnx stats.json; do
  aws s3 cp "$SRC/$f" "s3://$BUCKET/station/$V/$f" --only-show-errors
done

sed -e "s/__VERSION__/$V/g" -e "s/__BUCKET__/$BUCKET/g" -e "s/__THRESHOLD__/$THRESHOLD/g" \
  component/recipe.template.yaml > "$TMP/recipe.yaml"

echo "▶ creating $COMPONENT $V (threshold $THRESHOLD)"
aws greengrassv2 create-component-version --inline-recipe "fileb://$TMP/recipe.yaml" \
  --query '[componentName,componentVersion,status.componentState]' --output text

# Greengrass computes each artifact's digest; the version becomes DEPLOYABLE when it finishes
for _ in $(seq 1 30); do
  STATE="$(aws greengrassv2 describe-component --arn "$ARN" --query status.componentState --output text)"
  [ "$STATE" = "REQUESTED" ] || break
  sleep 2
done
if [ "$STATE" != "DEPLOYABLE" ]; then
  echo "✘ the version ended up in $STATE"
  aws greengrassv2 describe-component --arn "$ARN" --query status.message --output text || true
  exit 1
fi
echo "✔ $COMPONENT $V ready to deploy"
echo "Next: ./demo/deploy.sh $V all     (or ring-0 / ring-1)"
