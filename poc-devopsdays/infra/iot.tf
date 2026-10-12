# ── Anillos: un thing group por anillo ───────────────────────────────
resource "aws_iot_thing_group" "anillo" {
  for_each = toset(local.anillos)
  name     = each.key
}

# ── Rol de token exchange: lo que la bomba puede hacer en AWS ────────
data "aws_iam_policy_document" "confia_credenciales_iot" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["credentials.iot.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "tes" {
  name               = local.tes_rol
  assume_role_policy = data.aws_iam_policy_document.confia_credenciales_iot.json
}

# Lo mínimo del rol por defecto del instalador + leer los artefactos publicados (solo el prefijo estacion/)
resource "aws_iam_role_policy" "tes" {
  name = "estacion-dispositivo"
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
        Resource = "${aws_s3_bucket.artefactos.arn}/estacion/*"
      }
    ]
  })
}

resource "aws_iot_role_alias" "tes" {
  alias    = local.tes_alias
  role_arn = aws_iam_role.tes.arn
}

# ── Política de IoT de las bombas ────────────────────────────────────
# La mínima de la guía de Greengrass, con comodín bomba-* (Greengrass no admite variables de
# política de cosa) y permiso de publicar solo en estacion/eventos.
resource "aws_iot_policy" "bombas" {
  name = local.politica_bombas
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iot:Connect"
        Resource = "${local.arn_iot}:client/bomba-*"
      },
      {
        Effect = "Allow"
        Action = ["iot:Publish", "iot:Receive"]
        Resource = [
          "${local.arn_iot}:topic/$aws/things/bomba-*/greengrass/health/json",
          "${local.arn_iot}:topic/$aws/things/bomba-*/greengrassv2/health/json",
          "${local.arn_iot}:topic/$aws/things/bomba-*/jobs/*",
          "${local.arn_iot}:topic/$aws/things/bomba-*/shadow/*",
        ]
      },
      {
        Effect   = "Allow"
        Action   = "iot:Publish"
        Resource = "${local.arn_iot}:topic/${local.tema}"
      },
      {
        Effect = "Allow"
        Action = "iot:Subscribe"
        Resource = [
          "${local.arn_iot}:topicfilter/$aws/things/bomba-*/jobs/*",
          "${local.arn_iot}:topicfilter/$aws/things/bomba-*/shadow/*",
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

# La que el instalador crearía para el alias (camino sin Terraform en la identidad):
# la dejamos hecha para que las cinco bombas no compitan por crearla.
resource "aws_iot_policy" "tes_certificado" {
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

# ── Identidad de cada bomba (si gestionar_identidad = true) ──────────
# Thing + certificado + política + anillo. El certificado y su llave van a Parameter Store
# (SecureString); ./fleet/up.sh los baja en el primer arranque y los borra del disco al terminar.
locals {
  bombas_tf = var.gestionar_identidad ? var.bombas : {}
}

resource "aws_iot_thing" "bomba" {
  for_each = local.bombas_tf
  name     = each.key
}

resource "aws_iot_thing_group_membership" "bomba" {
  for_each         = local.bombas_tf
  thing_name       = aws_iot_thing.bomba[each.key].name
  thing_group_name = aws_iot_thing_group.anillo[each.value].name
}

resource "aws_iot_certificate" "bomba" {
  for_each = local.bombas_tf
  active   = true
}

resource "aws_iot_thing_principal_attachment" "bomba" {
  for_each  = local.bombas_tf
  thing     = aws_iot_thing.bomba[each.key].name
  principal = aws_iot_certificate.bomba[each.key].arn
}

resource "aws_iot_policy_attachment" "bomba" {
  for_each = local.bombas_tf
  policy   = aws_iot_policy.bombas.name
  target   = aws_iot_certificate.bomba[each.key].arn
}

resource "aws_ssm_parameter" "certificado" {
  for_each = local.bombas_tf
  name     = "/estacion/bombas/${each.key}/cert"
  type     = "SecureString"
  value    = aws_iot_certificate.bomba[each.key].certificate_pem
}

resource "aws_ssm_parameter" "llave" {
  for_each = local.bombas_tf
  name     = "/estacion/bombas/${each.key}/key"
  type     = "SecureString"
  value    = aws_iot_certificate.bomba[each.key].private_key
}

# Los endpoints de la cuenta: el nucleus los necesita cuando la identidad viene de afuera
data "aws_iot_endpoint" "datos" {
  endpoint_type = "iot:Data-ATS"
}

data "aws_iot_endpoint" "credenciales" {
  endpoint_type = "iot:CredentialProvider"
}

resource "aws_ssm_parameter" "endpoint_datos" {
  name  = "/estacion/iot/data_endpoint"
  type  = "String"
  value = data.aws_iot_endpoint.datos.endpoint_address
}

resource "aws_ssm_parameter" "endpoint_credenciales" {
  name  = "/estacion/iot/cred_endpoint"
  type  = "String"
  value = data.aws_iot_endpoint.credenciales.endpoint_address
}
