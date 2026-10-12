# ── Eventos: IoT Core → regla → CloudWatch Logs ──────────────────────
resource "aws_cloudwatch_log_group" "eventos" {
  name              = local.log_group
  retention_in_days = var.retencion_logs_dias
}

data "aws_iam_policy_document" "confia_regla" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["iot.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.cuenta]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["${local.arn_iot}:rule/${local.regla}"]
    }
  }
}

resource "aws_iam_role" "regla_a_logs" {
  name               = "EstacionIotToLogs"
  assume_role_policy = data.aws_iam_policy_document.confia_regla.json
}

resource "aws_iam_role_policy" "regla_a_logs" {
  name = "logs"
  role = aws_iam_role.regla_a_logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
      Resource = "${aws_cloudwatch_log_group.eventos.arn}:*"
    }]
  })
}

# arrived_ts = cuándo llegó a la nube; ts = cuándo decidió la bomba. La diferencia es el tiempo sin red.
resource "aws_iot_topic_rule" "eventos" {
  name        = local.regla
  enabled     = true
  sql         = "SELECT *, timestamp() AS arrived_ts FROM '${local.tema}'"
  sql_version = "2016-03-23"

  cloudwatch_logs {
    log_group_name = aws_cloudwatch_log_group.eventos.name
    role_arn       = aws_iam_role.regla_a_logs.arn
  }

  depends_on = [aws_iam_role_policy.regla_a_logs]
}

# ── Las señales de la bomba como métricas (namespace Estacion) ───────
# Mismos patrones que cloud/setup.sh (tests/test_infra_terraform.py lo verifica).
# CloudWatch no admite valor por defecto en las métricas con dimensiones.
locals {
  filtros = {
    # ¿qué decide?
    alertas = { metrica = "Alertas", patron = "{ ($.alert IS TRUE) && ($.device = *) }", valor = "1", dim = "Device", dim_valor = "$.device", defecto = "" }
    # ¿con cuánta seguridad? (el score contra el umbral de cada versión)
    score  = { metrica = "Score", patron = "{ ($.score = *) && ($.model_version = *) }", valor = "$.score", dim = "Version", dim_valor = "$.model_version", defecto = "" }
    umbral = { metrica = "Umbral", patron = "{ ($.threshold = *) && ($.model_version = *) }", valor = "$.threshold", dim = "Version", dim_valor = "$.model_version", defecto = "" }
    # ¿qué versión corre dónde?
    inferencias = { metrica = "Inferencias", patron = "{ $.model_version = * }", valor = "1", dim = "Version", dim_valor = "$.model_version", defecto = "" }
    # ¿se parece a lo que aprendió?
    entrada = { metrica = "InputZ", patron = "{ $.input_z = * }", valor = "$.input_z", dim = "", dim_valor = "", defecto = "" }
    # ¿en cuánto tiempo?
    latencia = { metrica = "LatencyMs", patron = "{ $.latency_ms = * }", valor = "$.latency_ms", dim = "", dim_valor = "", defecto = "" }
    # lo que dispara la vuelta: la bomba sonaba con falla (truth solo existe en la demo) y no avisó
    fallas = { metrica = "FallasNoOidas", patron = "{ ($.truth = \"anomaly\") && ($.alert IS FALSE) }", valor = "1", dim = "", dim_valor = "", defecto = "0" }
  }
}

resource "aws_cloudwatch_log_metric_filter" "senal" {
  for_each       = local.filtros
  name           = each.key
  log_group_name = aws_cloudwatch_log_group.eventos.name
  pattern        = each.value.patron

  metric_transformation {
    name          = each.value.metrica
    namespace     = local.ns
    value         = each.value.valor
    dimensions    = each.value.dim == "" ? null : { (each.value.dim) = each.value.dim_valor }
    default_value = each.value.defecto == "" ? null : each.value.defecto
  }
}

# ── Dashboard "estacion": el mismo JSON que usa cloud/setup.sh ───────
resource "aws_cloudwatch_dashboard" "estacion" {
  dashboard_name = "estacion"
  dashboard_body = replace(replace(replace(
    file("${path.module}/../cloud/dashboard.json"),
    "__REGION__", var.region),
    "__ACCOUNT__", local.cuenta),
  "__NS__", local.ns)
}

# ── La compuerta: alarma → Lambda → despliegue de la última versión buena al anillo 0 ──
data "archive_file" "vuelta" {
  type        = "zip"
  source_file = "${path.module}/../cloud/rollback_lambda.py"
  output_path = "${path.module}/.build/rollback.zip"
  # el mismo zip (y el mismo hash) en tu laptop y en Actions, aunque el archivo tenga otros permisos
  output_file_mode = "0644"
}

data "aws_iam_policy_document" "confia_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "vuelta" {
  name               = "EstacionRollback"
  assume_role_policy = data.aws_iam_policy_document.confia_lambda.json
}

resource "aws_iam_role_policy_attachment" "vuelta_logs" {
  role       = aws_iam_role.vuelta.name
  policy_arn = "arn:${local.part}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Mínimo para crear un despliegue de Greengrass (dependientes de greengrass:CreateDeployment) y leer un parámetro
resource "aws_iam_role_policy" "vuelta" {
  name = "vuelta"
  role = aws_iam_role.vuelta.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = "greengrass:CreateDeployment", Resource = "*" },
      {
        Effect   = "Allow"
        Action   = ["iot:CancelJob", "iot:CreateJob", "iot:DeleteThingShadow", "iot:DescribeJob", "iot:DescribeThing", "iot:DescribeThingGroup", "iot:GetThingShadow", "iot:UpdateJob", "iot:UpdateThingShadow"]
        Resource = "${local.arn_iot}:*"
      },
      { Effect = "Allow", Action = "ssm:GetParameter", Resource = aws_ssm_parameter.ultima_buena.arn }
    ]
  })
}

resource "aws_lambda_function" "vuelta" {
  function_name    = local.funcion
  role             = aws_iam_role.vuelta.arn
  runtime          = var.lambda_runtime
  handler          = "rollback_lambda.handler"
  filename         = data.archive_file.vuelta.output_path
  source_code_hash = data.archive_file.vuelta.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      THING_GROUP_ARN = aws_iot_thing_group.anillo["EstacionAnillo0"].arn
      COMPONENT       = local.componente
      LAST_GOOD_PARAM = local.parametro
    }
  }

  depends_on = [aws_iam_role_policy.vuelta, aws_iam_role_policy_attachment.vuelta_logs]
}

resource "aws_cloudwatch_metric_alarm" "fallas" {
  alarm_name          = local.alarma
  alarm_description   = "Fallas que ninguna bomba oyó: dispara la vuelta a la última versión buena"
  namespace           = local.ns
  metric_name         = "FallasNoOidas"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = var.umbral_alarma
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_lambda_function.vuelta.arn]
}

# La alarma solo puede invocar la función si la función se lo permite
resource "aws_lambda_permission" "alarma" {
  statement_id   = "cw-alarm"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.vuelta.function_name
  principal      = "lambda.alarms.cloudwatch.amazonaws.com"
  source_account = local.cuenta
  source_arn     = "arn:${local.part}:cloudwatch:${var.region}:${local.cuenta}:alarm:${local.alarma}"
}
