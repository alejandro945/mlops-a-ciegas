# ── The judge: shadow → bake → compare → promote or reject ───────────
# A candidate model never decides before this state machine compares it with the active one, on
# the same clips, on the canary. The alarm and the rollback Lambda (observability.tf) stay as the
# safety net for whatever gets past it. demo/judge.sh starts it.

resource "aws_sns_topic" "judge" {
  name = "station-judge"
}

data "aws_iam_policy_document" "trust_states" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "judge" {
  name               = "StationJudge"
  assume_role_policy = data.aws_iam_policy_document.trust_states.json
}

# The same Greengrass and IoT permissions as the rollback Lambda, plus the query, the parameter and the topic
resource "aws_iam_role_policy" "judge" {
  name = "judge"
  role = aws_iam_role.judge.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = "greengrass:CreateDeployment", Resource = "*" },
      {
        Effect   = "Allow"
        Action   = ["iot:CancelJob", "iot:CreateJob", "iot:DeleteThingShadow", "iot:DescribeJob", "iot:DescribeThing", "iot:DescribeThingGroup", "iot:GetThingShadow", "iot:UpdateJob", "iot:UpdateThingShadow"]
        Resource = "${local.iot_arn}:*"
      },
      { Effect = "Allow", Action = "logs:StartQuery", Resource = "${aws_cloudwatch_log_group.events.arn}:*" },
      { Effect = "Allow", Action = "logs:GetQueryResults", Resource = "*" },
      { Effect = "Allow", Action = "ssm:PutParameter", Resource = aws_ssm_parameter.last_good.arn },
      { Effect = "Allow", Action = "sns:Publish", Resource = aws_sns_topic.judge.arn }
    ]
  })
}

resource "aws_sfn_state_machine" "judge" {
  name     = local.judge
  role_arn = aws_iam_role.judge.arn
  definition = templatefile("${path.module}/../cloud/judge.asl.json", {
    ring0_arn = aws_iot_thing_group.ring["StationRing0"].arn
    ring1_arn = aws_iot_thing_group.ring["StationRing1"].arn
    component = local.component
    log_group = aws_cloudwatch_log_group.events.name
    last_good = local.last_good
    topic_arn = aws_sns_topic.judge.arn
  })

  depends_on = [aws_iam_role_policy.judge]
}
