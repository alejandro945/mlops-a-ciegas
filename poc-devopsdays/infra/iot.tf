# ── Rings: one thing group per ring ──────────────────────────────────
resource "aws_iot_thing_group" "ring" {
  for_each = toset(local.rings)
  name     = each.key
}

# ── Token exchange role: what a pump may do in AWS ───────────────────
data "aws_iam_policy_document" "trust_iot_credentials" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["credentials.iot.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "tes" {
  name               = local.tes_role
  assume_role_policy = data.aws_iam_policy_document.trust_iot_credentials.json
}

# The minimum of the installer's default role + reading the published artifacts (only the station/ prefix)
resource "aws_iam_role_policy" "tes" {
  name = "station-device"
  role = aws_iam_role.tes.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams", "s3:GetBucketLocation"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.artifacts.arn}/station/*"
      }
    ]
  })
}

resource "aws_iot_role_alias" "tes" {
  alias    = local.tes_alias
  role_arn = aws_iam_role.tes.arn
}

# ── IoT policy for the pumps ─────────────────────────────────────────
# The minimal one from the Greengrass guide, with a pump-* wildcard (Greengrass does not support
# thing policy variables) and permission to publish only on station/events.
resource "aws_iot_policy" "pumps" {
  name = local.pump_policy
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iot:Connect"
        Resource = "${local.iot_arn}:client/pump-*"
      },
      {
        Effect = "Allow"
        Action = ["iot:Publish", "iot:Receive"]
        Resource = [
          "${local.iot_arn}:topic/$aws/things/pump-*/greengrass/health/json",
          "${local.iot_arn}:topic/$aws/things/pump-*/greengrassv2/health/json",
          "${local.iot_arn}:topic/$aws/things/pump-*/jobs/*",
          "${local.iot_arn}:topic/$aws/things/pump-*/shadow/*",
        ]
      },
      {
        Effect   = "Allow"
        Action   = "iot:Publish"
        Resource = "${local.iot_arn}:topic/${local.topic}"
      },
      {
        Effect = "Allow"
        Action = "iot:Subscribe"
        Resource = [
          "${local.iot_arn}:topicfilter/$aws/things/pump-*/jobs/*",
          "${local.iot_arn}:topicfilter/$aws/things/pump-*/shadow/*",
        ]
      },
      {
        Effect   = "Allow"
        Action   = "iot:AssumeRoleWithCertificate"
        Resource = aws_iot_role_alias.tes.arn
      },
      {
        Effect   = "Allow"
        Action   = ["greengrass:GetComponentVersionArtifact", "greengrass:ResolveComponentCandidates", "greengrass:GetDeploymentConfiguration", "greengrass:ListThingGroupsForCoreDevice"]
        Resource = "*"
      }
    ]
  })
}

# The policy the installer would create for the alias (the path without Terraform-managed identity):
# we create it up front so the five pumps do not race to create it.
resource "aws_iot_policy" "tes_certificate" {
  name = "GreengrassTESCertificatePolicy${local.tes_alias}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iot:AssumeRoleWithCertificate"
      Resource = aws_iot_role_alias.tes.arn
    }]
  })
}

# ── Identity of each pump (when manage_identity = true) ──────────────
# Thing + certificate + policy + ring. The certificate and its key go to Parameter Store
# (SecureString); ./fleet/up.sh fetches them on first start and deletes them from disk when done.
locals {
  tf_pumps = var.manage_identity ? var.pumps : {}
}

resource "aws_iot_thing" "pump" {
  for_each = local.tf_pumps
  name     = each.key
}

resource "aws_iot_thing_group_membership" "pump" {
  for_each         = local.tf_pumps
  thing_name       = aws_iot_thing.pump[each.key].name
  thing_group_name = aws_iot_thing_group.ring[each.value].name
}

resource "aws_iot_certificate" "pump" {
  for_each = local.tf_pumps
  active   = true
}

resource "aws_iot_thing_principal_attachment" "pump" {
  for_each  = local.tf_pumps
  thing     = aws_iot_thing.pump[each.key].name
  principal = aws_iot_certificate.pump[each.key].arn
}

resource "aws_iot_policy_attachment" "pump" {
  for_each = local.tf_pumps
  policy   = aws_iot_policy.pumps.name
  target   = aws_iot_certificate.pump[each.key].arn
}

resource "aws_ssm_parameter" "certificate" {
  for_each = local.tf_pumps
  name     = "/station/pumps/${each.key}/cert"
  type     = "SecureString"
  value    = aws_iot_certificate.pump[each.key].certificate_pem
}

resource "aws_ssm_parameter" "key" {
  for_each = local.tf_pumps
  name     = "/station/pumps/${each.key}/key"
  type     = "SecureString"
  value    = aws_iot_certificate.pump[each.key].private_key
}

# The account's endpoints: the nucleus needs them when the identity comes from outside
data "aws_iot_endpoint" "data" {
  endpoint_type = "iot:Data-ATS"
}

data "aws_iot_endpoint" "cred" {
  endpoint_type = "iot:CredentialProvider"
}

resource "aws_ssm_parameter" "data_endpoint" {
  name  = "/station/iot/data_endpoint"
  type  = "String"
  value = data.aws_iot_endpoint.data.endpoint_address
}

resource "aws_ssm_parameter" "cred_endpoint" {
  name  = "/station/iot/cred_endpoint"
  type  = "String"
  value = data.aws_iot_endpoint.cred.endpoint_address
}
