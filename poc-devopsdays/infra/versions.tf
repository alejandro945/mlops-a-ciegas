# PoC · The station · infrastructure as code
#
# The same as cloud/setup.sh, plus the identity of the five pumps and the EC2 that hosts them.
# Remote state in S3 (backend.tf): it holds the pumps' private keys, so it never goes into the
# repository. See README.md in this folder.

terraform {
  required_version = ">= 1.11" # use_lockfile in the S3 backend

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
    tags = var.tags
  }
}
