data "aws_caller_identity" "me" {}
data "aws_partition" "p" {}

locals {
  account = data.aws_caller_identity.me.account_id
  part    = data.aws_partition.p.partition
  bucket  = var.bucket_name != "" ? var.bucket_name : "station-${local.account}-${var.region}"

  # The same names as cloud/setup.sh, demo/*.sh and the slides
  component   = "com.station.Listener"
  rings       = ["StationRing0", "StationRing1"]
  topic       = "station/events"
  log_group   = "/station/events"
  ns          = "Station"
  rule        = "station_events"
  alarm       = "station-missed-faults"
  function    = "station-rollback"
  last_good   = "/station/last_good_version"
  tes_role    = "GreengrassV2TokenExchangeRole"
  tes_alias   = "GreengrassCoreTokenExchangeRoleAlias"
  pump_policy = "StationThingPolicy"

  iot_arn = "arn:${local.part}:iot:${var.region}:${local.account}"
}

# ── Artifacts bucket ─────────────────────────────────────────────────
# publish.sh uploads each version to station/<version>/; Greengrass computes the digest when it
# creates the component version.
resource "aws_s3_bucket" "artifacts" {
  bucket        = local.bucket
  force_destroy = var.force_destroy_bucket
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ── Last good version (read by the Lambda; updated by deploy.sh) ─────
resource "aws_ssm_parameter" "last_good" {
  name  = local.last_good
  type  = "String"
  value = "1.0.0"

  lifecycle {
    ignore_changes = [value] # ./demo/deploy.sh changes it, not Terraform
  }
}
