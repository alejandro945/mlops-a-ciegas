# Remote state in S3, shared between your laptop and GitHub Actions.
# The bucket is created by infra/github/ (once). Partial configuration: the bucket and the region
# come through -backend-config: on your laptop, `terraform init -backend-config=backend.hcl`
# (written by infra/github/connect-repo.sh); in Actions, from the repo variables.
#
# The state holds the pumps' private keys: the bucket is private, encrypted, versioned and only
# accepts TLS. use_lockfile keeps two applies from stepping on each other (no DynamoDB).
terraform {
  backend "s3" {
    key          = "poc-devopsdays/infra.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}
