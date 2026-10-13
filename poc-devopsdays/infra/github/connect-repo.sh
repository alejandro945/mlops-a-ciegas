#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Connects the GitHub repo to what `terraform apply` created in this folder:
#   · repo variables: AWS_REGION, TF_STATE_BUCKET, AWS_ROLE_PLAN, AWS_ROLE_APPLY
#     (ALARM_THRESHOLD is optional; set it by hand to override the default of 8)
#   · environment aws-poc: apply and destroy only run from main (and with your approval, if
#     your GitHub plan allows it)
#   · ../backend.hcl, so your laptop uses the same state as Actions
#
#  Usage:  ./infra/github/connect-repo.sh        (needs gh logged in, with admin rights on the repo)
#
#  Environment approvals work on public repos with any GitHub plan; on a private one they need
#  GitHub Pro or Team. Without them, the environment is created with no reviewer and the
#  script says so.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

out() { terraform output -raw "$1"; }
REPO="$(out repo)"; REGION="$(out region)"; BUCKET="$(out state_bucket)"
PLAN="$(out plan_role)"; APPLY="$(out apply_role)"; ENV="$(out environment)"

echo "▶ variables of $REPO"
gh variable set AWS_REGION      -R "$REPO" -b "$REGION"
gh variable set TF_STATE_BUCKET -R "$REPO" -b "$BUCKET"
gh variable set AWS_ROLE_PLAN   -R "$REPO" -b "$PLAN"
gh variable set AWS_ROLE_APPLY  -R "$REPO" -b "$APPLY"

echo "▶ environment $ENV (main only)"
ME="$(gh api user --jq .id)"
body() {
  printf '{"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}%s}' "$1"
}
if ! gh api -X PUT "repos/$REPO/environments/$ENV" --input - >/dev/null 2>&1 \
     <<<"$(body ",\"reviewers\":[{\"type\":\"User\",\"id\":$ME}]")"; then
  gh api -X PUT "repos/$REPO/environments/$ENV" --input - >/dev/null <<<"$(body "")"
  echo "  ⚠ GitHub did not accept the reviewer (private repo without Pro or Team): the environment only restricts to main."
  echo "    Apply is still manual: Actions → infra → Run workflow → apply."
fi
if ! gh api "repos/$REPO/environments/$ENV/deployment-branch-policies" --jq '.branch_policies[].name' | grep -qx main; then
  gh api -X POST "repos/$REPO/environments/$ENV/deployment-branch-policies" -f name=main -f type=branch >/dev/null
fi

cat > ../backend.hcl <<EOF
bucket = "$BUCKET"
region = "$REGION"
EOF
echo "▶ wrote infra/backend.hcl"
echo "✔ done. On your laptop: terraform -chdir=infra init -reconfigure -backend-config=backend.hcl"
