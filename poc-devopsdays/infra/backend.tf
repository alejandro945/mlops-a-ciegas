# Estado remoto en S3, compartido entre tu laptop y GitHub Actions.
# El bucket lo crea infra/github/ (una vez). Configuración parcial: el bucket y la región llegan por
# -backend-config: en tu laptop, `terraform init -backend-config=backend.hcl` (lo escribe
# infra/github/conectar-repo.sh); en Actions, las variables del repo.
#
# El estado guarda las llaves privadas de las bombas: el bucket es privado, cifrado, versionado
# y solo acepta TLS. use_lockfile evita que dos apply se pisen (sin DynamoDB).
terraform {
  backend "s3" {
    key          = "poc-devopsdays/infra.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}
