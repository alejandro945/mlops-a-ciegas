# ─────────────────────────────────────────────────────────────────────
#  What GitHub Actions needs in AWS to run infra/. Applied once, from your laptop, with an
#  administrator user of the test account.
#
#   · the bucket for the infra/ state (private, encrypted, versioned, TLS only)
#   · GitHub's OIDC provider: Actions gets into AWS with no keys stored in the repo
#   · github-station-plan: read only; assumed by a PR or a branch of the repo
#   · github-station-apply: creates and destroys the PoC; only a job in the aws-poc environment,
#     which asks for your approval. It can do everything except IAM, and in IAM it only touches
#     the PoC's roles
#
#  Local state (terraform.tfstate in this folder, outside the repo). It holds no secrets.
#  Then: ./connect-repo.sh sets the variables and the environment on GitHub.
# ─────────────────────────────────────────────────────────────────────
terraform {
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project = "mlops-a-ciegas"
      talk    = "devopsdays-bogota-2026"
      part    = "github"
    }
  }
}

variable "region" {
  description = "Region of the PoC and of the state bucket."
  type        = string
  default     = "us-east-1"
}

variable "repo" {
  description = "The GitHub repo as owner/name, for example alejandro945/mlops-a-ciegas."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$", var.repo))
    error_message = "Write the repo as owner/name."
  }
}

variable "sub_prefix" {
  description = <<-EOT
    The prefix of the OIDC token's sub when the repo uses GitHub's immutable format
    (repo:owner@id/name@id). It comes from:
      gh api repos/<owner>/<repo>/actions/oidc/customization/sub --jq .sub_claim_prefix
    Empty = only the classic format repo:owner/name.
  EOT
  type        = string
  default     = ""
}

variable "environment" {
  description = "GitHub environment that may assume the apply role (with approval)."
  type        = string
  default     = "aws-poc"
}

variable "create_oidc_provider" {
  description = "false if the account already has the OIDC provider for token.actions.githubusercontent.com."
  type        = bool
  default     = true
}

data "aws_caller_identity" "me" {}
data "aws_partition" "p" {}

locals {
  account  = data.aws_caller_identity.me.account_id
  part     = data.aws_partition.p.partition
  bucket   = "station-tfstate-${local.account}-${var.region}"
  key      = "poc-devopsdays/infra.tfstate"
  oidc     = "token.actions.githubusercontent.com"
  oidc_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : "arn:${local.part}:iam::${local.account}:oidc-provider/${local.oidc}"
  iam_arn  = "arn:${local.part}:iam::${local.account}"

  # GitHub signs the sub as repo:owner/name or, with the immutable format, repo:owner@id/name@id
  prefixes = compact(["repo:${var.repo}", var.sub_prefix])
}

# ── The state bucket ─────────────────────────────────────────────────
# force_destroy: renaming the bucket replaces it, and Terraform must be able to delete the old
# one even though it is versioned and not empty. Back up the state before doing that.
resource "aws_s3_bucket" "state" {
  bucket        = local.bucket
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Old versions of the state are deleted after 90 days
resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    id     = "old-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
  depends_on = [aws_s3_bucket_versioning.state]
}

resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "TLSOnly"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.state]
}

# ── OIDC: GitHub Actions gets in without keys ────────────────────────
# AWS no longer uses the thumbprint for this provider (it trusts GitHub's CA).
resource "aws_iam_openid_connect_provider" "github" {
  count          = var.create_oidc_provider ? 1 : 0
  url            = "https://${local.oidc}"
  client_id_list = ["sts.amazonaws.com"]
}

# ── Plan role: read only, from a PR or a branch of the repo ──────────
# PRs from a fork get no OIDC token: they cannot assume it.
data "aws_iam_policy_document" "trust_plan" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.oidc_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "${local.oidc}:sub"
      values   = flatten([for p in local.prefixes : ["${p}:pull_request", "${p}:ref:refs/heads/*"]])
    }
  }
}

resource "aws_iam_role" "plan" {
  name                 = "github-station-plan"
  description          = "GitHub Actions: terraform plan of poc-devopsdays/infra (read only)"
  assume_role_policy   = data.aws_iam_policy_document.trust_plan.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "plan_readonly" {
  role       = aws_iam_role.plan.name
  policy_arn = "arn:${local.part}:iam::aws:policy/ReadOnlyAccess"
}

# plan also writes the state lock and reads the pumps' SecureStrings
resource "aws_iam_role_policy" "plan" {
  name = "state-and-parameters"
  role = aws_iam_role.plan.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.state.arn}/${local.key}.tflock"
      },
      {
        Effect    = "Allow"
        Action    = "kms:Decrypt"
        Resource  = "*"
        Condition = { StringEquals = { "kms:ViaService" = "ssm.${var.region}.amazonaws.com" } }
      }
    ]
  })
}

# ── Apply role: only from the environment (with approval) ────────────
data "aws_iam_policy_document" "trust_apply" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.oidc_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc}:sub"
      values   = [for p in local.prefixes : "${p}:environment:${var.environment}"]
    }
  }
}

resource "aws_iam_role" "apply" {
  name                 = "github-station-apply"
  description          = "GitHub Actions: terraform apply and destroy of poc-devopsdays/infra"
  assume_role_policy   = data.aws_iam_policy_document.trust_apply.json
  max_session_duration = 3600
}

# Everything except IAM: S3, IoT, Greengrass, SSM, CloudWatch, Lambda and EC2
resource "aws_iam_role_policy_attachment" "apply_power" {
  role       = aws_iam_role.apply.name
  policy_arn = "arn:${local.part}:iam::aws:policy/PowerUserAccess"
}

# In IAM, only the PoC's four roles and its instance profile. The names are the ones in infra/*.tf;
# github-station-* is left out: the role cannot grant itself more permissions.
resource "aws_iam_role_policy" "apply_iam" {
  name = "poc-roles-only"
  role = aws_iam_role.apply.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Roles"
        Effect = "Allow"
        Action = [
          "iam:CreateRole", "iam:DeleteRole", "iam:GetRole", "iam:UpdateRole", "iam:UpdateRoleDescription",
          "iam:UpdateAssumeRolePolicy", "iam:TagRole", "iam:UntagRole", "iam:ListRoleTags",
          "iam:PutRolePolicy", "iam:GetRolePolicy", "iam:DeleteRolePolicy", "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies", "iam:ListInstanceProfilesForRole", "iam:PassRole"
        ]
        Resource = ["${local.iam_arn}:role/GreengrassV2TokenExchangeRole", "${local.iam_arn}:role/Station*"]
      },
      {
        Sid      = "ManagedPolicies"
        Effect   = "Allow"
        Action   = ["iam:AttachRolePolicy", "iam:DetachRolePolicy"]
        Resource = ["${local.iam_arn}:role/GreengrassV2TokenExchangeRole", "${local.iam_arn}:role/Station*"]
        Condition = {
          ArnEquals = {
            "iam:PolicyARN" = [
              "arn:${local.part}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
              "arn:${local.part}:iam::aws:policy/AmazonSSMManagedInstanceCore"
            ]
          }
        }
      },
      {
        Sid    = "Ec2InstanceProfile"
        Effect = "Allow"
        Action = [
          "iam:CreateInstanceProfile", "iam:DeleteInstanceProfile", "iam:GetInstanceProfile",
          "iam:AddRoleToInstanceProfile", "iam:RemoveRoleFromInstanceProfile",
          "iam:TagInstanceProfile", "iam:UntagInstanceProfile", "iam:ListInstanceProfileTags"
        ]
        Resource = "${local.iam_arn}:instance-profile/StationHost"
      }
    ]
  })
}

# ── Outputs ──────────────────────────────────────────────────────────
output "state_bucket" {
  value = aws_s3_bucket.state.bucket
}

output "plan_role" {
  value = aws_iam_role.plan.arn
}

output "apply_role" {
  value = aws_iam_role.apply.arn
}

output "repo" {
  value = var.repo
}

output "region" {
  value = var.region
}

output "environment" {
  value = var.environment
}
