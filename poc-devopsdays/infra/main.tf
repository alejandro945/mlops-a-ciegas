data "aws_caller_identity" "yo" {}
data "aws_partition" "p" {}

locals {
  cuenta = data.aws_caller_identity.yo.account_id
  part   = data.aws_partition.p.partition
  bucket = var.nombre_bucket != "" ? var.nombre_bucket : "estacion-${local.cuenta}-${var.region}"

  # Los mismos nombres que cloud/setup.sh, demo/*.sh y las láminas
  componente      = "com.estacion.Escucha"
  anillos         = ["EstacionAnillo0", "EstacionAnillo1"]
  tema            = "estacion/eventos"
  log_group       = "/estacion/eventos"
  ns              = "Estacion"
  regla           = "estacion_eventos"
  alarma          = "estacion-fallas-no-oidas"
  funcion         = "estacion-rollback"
  parametro       = "/estacion/last_good_version"
  tes_rol         = "GreengrassV2TokenExchangeRole"
  tes_alias       = "GreengrassCoreTokenExchangeRoleAlias"
  politica_bombas = "EstacionThingPolicy"

  arn_iot = "arn:${local.part}:iot:${var.region}:${local.cuenta}"
}

# ── Bucket de artefactos ─────────────────────────────────────────────
# publish.sh sube cada versión a estacion/<versión>/; Greengrass calcula el digest al crear la versión.
resource "aws_s3_bucket" "artefactos" {
  bucket        = local.bucket
  force_destroy = var.forzar_borrado_bucket
}

resource "aws_s3_bucket_public_access_block" "artefactos" {
  bucket                  = aws_s3_bucket.artefactos.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artefactos" {
  bucket = aws_s3_bucket.artefactos.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ── Última versión buena (la lee la Lambda; deploy.sh la actualiza) ──
resource "aws_ssm_parameter" "ultima_buena" {
  name  = local.parametro
  type  = "String"
  value = "1.0.0"

  lifecycle {
    ignore_changes = [value] # la cambia ./demo/deploy.sh, no Terraform
  }
}
