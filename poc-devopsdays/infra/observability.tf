# ── Events: IoT Core → rule → CloudWatch Logs ────────────────────────
resource "aws_cloudwatch_log_group" "events" {
  name              = local.log_group
  retention_in_days = var.log_retention_days
}

data "aws_iam_policy_document" "trust_rule" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["iot.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["${local.iot_arn}:rule/${local.rule}"]
    }
  }
}

resource "aws_iam_role" "rule_to_logs" {
  name               = "StationIotToLogs"
  assume_role_policy = data.aws_iam_policy_document.trust_rule.json
}

resource "aws_iam_role_policy" "rule_to_logs" {
  name = "logs"
  role = aws_iam_role.rule_to_logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
      Resource = "${aws_cloudwatch_log_group.events.arn}:*"
    }]
  })
}

# arrived_ts = when it reached the cloud; ts = when the pump decided. The difference is the time offline.
resource "aws_iot_topic_rule" "events" {
  name        = local.rule
  enabled     = true
  sql         = "SELECT *, timestamp() AS arrived_ts FROM '${local.topic}'"
  sql_version = "2016-03-23"

  cloudwatch_logs {
    log_group_name = aws_cloudwatch_log_group.events.name
    role_arn       = aws_iam_role.rule_to_logs.arn
  }

  depends_on = [aws_iam_role_policy.rule_to_logs]
}

# ── The pump's signals as metrics (namespace Station) ────────────────
# Same patterns as cloud/setup.sh (tests/test_infra_terraform.py checks it).
# CloudWatch does not allow a default value on metrics with dimensions.
locals {
  filters = {
    # what does it decide?
    alerts = { metric = "Alerts", pattern = "{ ($.alert IS TRUE) && ($.device = *) }", value = "1", dim = "Device", dim_value = "$.device", default = "" }
    # how sure is it? (the score against each version's threshold)
    score     = { metric = "Score", pattern = "{ ($.score = *) && ($.model_version = *) }", value = "$.score", dim = "Version", dim_value = "$.model_version", default = "" }
    threshold = { metric = "Threshold", pattern = "{ ($.threshold = *) && ($.model_version = *) }", value = "$.threshold", dim = "Version", dim_value = "$.model_version", default = "" }
    # which version runs where?
    inferences = { metric = "Inferences", pattern = "{ $.model_version = * }", value = "1", dim = "Version", dim_value = "$.model_version", default = "" }
    # does it look like what it learned?
    input = { metric = "InputZ", pattern = "{ $.input_z = * }", value = "$.input_z", dim = "", dim_value = "", default = "" }
    # … per pump, so a single drifting (or tampered) sensor does not hide in the fleet average
    input_by_device = { metric = "InputZ", pattern = "{ ($.input_z = *) && ($.device = *) }", value = "$.input_z", dim = "Device", dim_value = "$.device", default = "" }
    # how fast?
    latency = { metric = "LatencyMs", pattern = "{ $.latency_ms = * }", value = "$.latency_ms", dim = "", dim_value = "", default = "" }
    # what triggers the rollback: the pump sounded faulty (truth only exists in the demo) and did not alert
    missed_faults = { metric = "MissedFaults", pattern = "{ ($.truth = \"anomaly\") && ($.alert IS FALSE) }", value = "1", dim = "", dim_value = "", default = "0" }
  }
}

resource "aws_cloudwatch_log_metric_filter" "signal" {
  for_each       = local.filters
  name           = each.key
  log_group_name = aws_cloudwatch_log_group.events.name
  pattern        = each.value.pattern

  metric_transformation {
    name          = each.value.metric
    namespace     = local.ns
    value         = each.value.value
    dimensions    = each.value.dim == "" ? null : { (each.value.dim) = each.value.dim_value }
    default_value = each.value.default == "" ? null : each.value.default
  }
}

# ── Dashboard "station": the same JSON cloud/setup.sh uses ───────────
resource "aws_cloudwatch_dashboard" "station" {
  dashboard_name = "station"
  dashboard_body = replace(replace(replace(
    file("${path.module}/../cloud/dashboard.json"),
    "__REGION__", var.region),
    "__ACCOUNT__", local.account),
  "__NS__", local.ns)
}

# ── The gate: alarm → Lambda → deploy the last good version to ring 0 ──
data "archive_file" "rollback" {
  type        = "zip"
  source_file = "${path.module}/../cloud/rollback_lambda.py"
  output_path = "${path.module}/.build/rollback.zip"
  # the same zip (and the same hash) on your laptop and in Actions, even if the file has other permissions
  output_file_mode = "0644"
}

data "aws_iam_policy_document" "trust_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "rollback" {
  name               = "StationRollback"
  assume_role_policy = data.aws_iam_policy_document.trust_lambda.json
}

resource "aws_iam_role_policy_attachment" "rollback_logs" {
  role       = aws_iam_role.rollback.name
  policy_arn = "arn:${local.part}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# The minimum to create a Greengrass deployment (greengrass:CreateDeployment dependencies) and read one parameter
resource "aws_iam_role_policy" "rollback" {
  name = "rollback"
  role = aws_iam_role.rollback.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = "greengrass:CreateDeployment", Resource = "*" },
      {
        Effect   = "Allow"
        Action   = ["iot:CancelJob", "iot:CreateJob", "iot:DeleteThingShadow", "iot:DescribeJob", "iot:DescribeThing", "iot:DescribeThingGroup", "iot:GetThingShadow", "iot:UpdateJob", "iot:UpdateThingShadow"]
        Resource = "${local.iot_arn}:*"
      },
      { Effect = "Allow", Action = "ssm:GetParameter", Resource = aws_ssm_parameter.last_good.arn }
    ]
  })
}

resource "aws_lambda_function" "rollback" {
  function_name    = local.function
  role             = aws_iam_role.rollback.arn
  runtime          = var.lambda_runtime
  handler          = "rollback_lambda.handler"
  filename         = data.archive_file.rollback.output_path
  source_code_hash = data.archive_file.rollback.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      THING_GROUP_ARN = aws_iot_thing_group.ring["StationRing0"].arn
      COMPONENT       = local.component
      LAST_GOOD_PARAM = local.last_good
    }
  }

  depends_on = [aws_iam_role_policy.rollback, aws_iam_role_policy_attachment.rollback_logs]
}

resource "aws_cloudwatch_metric_alarm" "missed_faults" {
  alarm_name          = local.alarm
  alarm_description   = "Faults no pump heard: triggers the rollback to the last good version"
  namespace           = local.ns
  metric_name         = "MissedFaults"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = var.alarm_threshold
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_lambda_function.rollback.arn]
}

# The alarm can only invoke the function if the function allows it
resource "aws_lambda_permission" "alarm" {
  statement_id   = "cw-alarm"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.rollback.function_name
  principal      = "lambda.alarms.cloudwatch.amazonaws.com"
  source_account = local.account
  source_arn     = "arn:${local.part}:cloudwatch:${var.region}:${local.account}:alarm:${local.alarm}"
}
