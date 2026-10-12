# ─────────────────────────────────────────────────────────────────────
#  Lo que GitHub Actions necesita en AWS para correr infra/. Se aplica una vez, desde tu laptop,
#  con un usuario administrador de la cuenta de pruebas.
#
#   · el bucket del estado de infra/ (privado, cifrado, versionado, solo TLS)
#   · el proveedor OIDC de GitHub: Actions entra a AWS sin llaves guardadas en el repo
#   · github-estacion-plan: solo lectura; lo asume un PR o una rama del repo
#   · github-estacion-apply: crea y borra la PoC; solo un job del environment aws-poc, que pide
#     tu aprobación. Puede todo menos IAM, y en IAM solo toca los roles de la PoC
#
#  Estado local (terraform.tfstate en esta carpeta, fuera del repo). No guarda secretos.
#  Después: ./conectar-repo.sh deja las variables y el environment en GitHub.
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
      proyecto = "mlops-a-ciegas"
      charla   = "devopsdays-bogota-2026"
      parte    = "github"
    }
  }
}

variable "region" {
  description = "Región de la PoC y del bucket del estado."
  type        = string
  default     = "us-east-1"
}

variable "repo" {
  description = "El repo de GitHub como dueño/nombre, por ejemplo alejandro945/mlops-a-ciegas."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$", var.repo))
    error_message = "Escribe el repo como dueño/nombre."
  }
}

variable "environment" {
  description = "Environment de GitHub que puede asumir el rol de apply (con aprobación)."
  type        = string
  default     = "aws-poc"
}

variable "crear_proveedor_oidc" {
  description = "false si la cuenta ya tiene el proveedor OIDC de token.actions.githubusercontent.com."
  type        = bool
  default     = true
}

data "aws_caller_identity" "yo" {}
data "aws_partition" "p" {}

locals {
  cuenta   = data.aws_caller_identity.yo.account_id
  part     = data.aws_partition.p.partition
  bucket   = "estacion-tfstate-${local.cuenta}-${var.region}"
  llave    = "poc-devopsdays/infra.tfstate"
  oidc     = "token.actions.githubusercontent.com"
  oidc_arn = var.crear_proveedor_oidc ? aws_iam_openid_connect_provider.github[0].arn : "arn:${local.part}:iam::${local.cuenta}:oidc-provider/${local.oidc}"
  arn_iam  = "arn:${local.part}:iam::${local.cuenta}"
}

# ── El bucket del estado ─────────────────────────────────────────────
resource "aws_s3_bucket" "estado" {
  bucket = local.bucket

  lifecycle {
    prevent_destroy = true # sin este bucket, Terraform pierde la cuenta de lo que creó
  }
}

resource "aws_s3_bucket_versioning" "estado" {
  bucket = aws_s3_bucket.estado.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "estado" {
  bucket = aws_s3_bucket.estado.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "estado" {
  bucket                  = aws_s3_bucket.estado.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "estado" {
  bucket = aws_s3_bucket.estado.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Las versiones viejas del estado se borran a los 90 días
resource "aws_s3_bucket_lifecycle_configuration" "estado" {
  bucket = aws_s3_bucket.estado.id
  rule {
    id     = "versiones-viejas"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
  depends_on = [aws_s3_bucket_versioning.estado]
}

resource "aws_s3_bucket_policy" "estado" {
  bucket = aws_s3_bucket.estado.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "SoloTLS"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.estado.arn, "${aws_s3_bucket.estado.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.estado]
}

# ── OIDC: GitHub Actions entra sin llaves ────────────────────────────
# AWS ya no usa el thumbprint para este proveedor (confía en la CA de GitHub).
resource "aws_iam_openid_connect_provider" "github" {
  count          = var.crear_proveedor_oidc ? 1 : 0
  url            = "https://${local.oidc}"
  client_id_list = ["sts.amazonaws.com"]
}

# ── Rol de plan: solo lectura, desde un PR o una rama del repo ───────
# Los PR que vienen de un fork no reciben token OIDC: no pueden asumirlo.
data "aws_iam_policy_document" "confia_plan" {
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
      values   = ["repo:${var.repo}:pull_request", "repo:${var.repo}:ref:refs/heads/*"]
    }
  }
}

resource "aws_iam_role" "plan" {
  name                 = "github-estacion-plan"
  description          = "GitHub Actions: terraform plan de poc-devopsdays/infra (solo lectura)"
  assume_role_policy   = data.aws_iam_policy_document.confia_plan.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "plan_lectura" {
  role       = aws_iam_role.plan.name
  policy_arn = "arn:${local.part}:iam::aws:policy/ReadOnlyAccess"
}

# plan también escribe el candado del estado y lee los SecureString de las bombas
resource "aws_iam_role_policy" "plan" {
  name = "estado-y-parametros"
  role = aws_iam_role.plan.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.estado.arn}/${local.llave}.tflock"
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

# ── Rol de apply: solo desde el environment (con aprobación) ─────────
data "aws_iam_policy_document" "confia_apply" {
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
      values   = ["repo:${var.repo}:environment:${var.environment}"]
    }
  }
}

resource "aws_iam_role" "apply" {
  name                 = "github-estacion-apply"
  description          = "GitHub Actions: terraform apply y destroy de poc-devopsdays/infra"
  assume_role_policy   = data.aws_iam_policy_document.confia_apply.json
  max_session_duration = 3600
}

# Todo menos IAM: S3, IoT, Greengrass, SSM, CloudWatch, Lambda y EC2
resource "aws_iam_role_policy_attachment" "apply_power" {
  role       = aws_iam_role.apply.name
  policy_arn = "arn:${local.part}:iam::aws:policy/PowerUserAccess"
}

# En IAM, solo los cuatro roles de la PoC y su instance profile. Los nombres son los de infra/*.tf;
# github-estacion-* queda afuera: el rol no puede darse más permisos.
resource "aws_iam_role_policy" "apply_iam" {
  name = "solo-los-roles-de-la-poc"
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
        Resource = ["${local.arn_iam}:role/GreengrassV2TokenExchangeRole", "${local.arn_iam}:role/Estacion*"]
      },
      {
        Sid      = "PoliticasAdministradas"
        Effect   = "Allow"
        Action   = ["iam:AttachRolePolicy", "iam:DetachRolePolicy"]
        Resource = ["${local.arn_iam}:role/GreengrassV2TokenExchangeRole", "${local.arn_iam}:role/Estacion*"]
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
        Sid    = "PerfilDeLaEC2"
        Effect = "Allow"
        Action = [
          "iam:CreateInstanceProfile", "iam:DeleteInstanceProfile", "iam:GetInstanceProfile",
          "iam:AddRoleToInstanceProfile", "iam:RemoveRoleFromInstanceProfile",
          "iam:TagInstanceProfile", "iam:UntagInstanceProfile", "iam:ListInstanceProfileTags"
        ]
        Resource = "${local.arn_iam}:instance-profile/EstacionHost"
      }
    ]
  })
}

# ── Salidas ──────────────────────────────────────────────────────────
output "bucket_estado" {
  value = aws_s3_bucket.estado.bucket
}

output "rol_plan" {
  value = aws_iam_role.plan.arn
}

output "rol_apply" {
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
