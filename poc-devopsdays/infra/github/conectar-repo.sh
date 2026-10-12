#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  Conecta el repo de GitHub con lo que creó `terraform apply` en esta carpeta:
#   · variables del repo: AWS_REGION, TF_STATE_BUCKET, AWS_ROLE_PLAN, AWS_ROLE_APPLY
#   · environment aws-poc: el apply y el destroy solo corren desde main (y con tu aprobación, si
#     el plan de GitHub lo permite)
#   · ../backend.hcl, para que tu laptop use el mismo estado que Actions
#
#  Uso:  ./infra/github/conectar-repo.sh        (necesita gh con sesión y permiso de admin en el repo)
#
#  Las aprobaciones de un environment funcionan en repos públicos con cualquier plan de GitHub;
#  en uno privado piden GitHub Pro o Team. Si no hay, el environment se crea sin revisor y el
#  script lo avisa.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

out() { terraform output -raw "$1"; }
REPO="$(out repo)"; REGION="$(out region)"; BUCKET="$(out bucket_estado)"
PLAN="$(out rol_plan)"; APPLY="$(out rol_apply)"; ENV="$(out environment)"

echo "▶ variables de $REPO"
gh variable set AWS_REGION      -R "$REPO" -b "$REGION"
gh variable set TF_STATE_BUCKET -R "$REPO" -b "$BUCKET"
gh variable set AWS_ROLE_PLAN   -R "$REPO" -b "$PLAN"
gh variable set AWS_ROLE_APPLY  -R "$REPO" -b "$APPLY"

echo "▶ environment $ENV (solo main)"
YO="$(gh api user --jq .id)"
cuerpo() {
  printf '{"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}%s}' "$1"
}
if ! gh api -X PUT "repos/$REPO/environments/$ENV" --input - >/dev/null 2>&1 \
     <<<"$(cuerpo ",\"reviewers\":[{\"type\":\"User\",\"id\":$YO}]")"; then
  gh api -X PUT "repos/$REPO/environments/$ENV" --input - >/dev/null <<<"$(cuerpo "")"
  echo "  ⚠ GitHub no aceptó el revisor (repo privado sin Pro o Team): el environment solo limita a main."
  echo "    El apply igual es manual: Actions → infra → Run workflow → apply."
fi
if ! gh api "repos/$REPO/environments/$ENV/deployment-branch-policies" --jq '.branch_policies[].name' | grep -qx main; then
  gh api -X POST "repos/$REPO/environments/$ENV/deployment-branch-policies" -f name=main -f type=branch >/dev/null
fi

cat > ../backend.hcl <<EOF
bucket = "$BUCKET"
region = "$REGION"
EOF
echo "▶ escrito infra/backend.hcl"
echo "✔ listo. En tu laptop: terraform -chdir=infra init -backend-config=backend.hcl"
