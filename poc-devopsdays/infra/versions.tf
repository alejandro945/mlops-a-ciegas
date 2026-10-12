# PoC · La estación · infraestructura como código
#
# Lo mismo que cloud/setup.sh, más la identidad de las cinco bombas y la EC2 que las hospeda.
# Estado remoto en S3 (backend.tf): guarda las llaves privadas de las bombas, así que nunca va
# al repositorio. Ver README.md de esta carpeta.

terraform {
  required_version = ">= 1.11" # use_lockfile del backend S3

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = var.etiquetas
  }
}
