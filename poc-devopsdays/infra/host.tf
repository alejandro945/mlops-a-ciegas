# ── The EC2 that hosts the five pumps ────────────────────────────────
# Greengrass in Docker needs a Linux host. Access is through Session Manager only (no inbound
# ports, no key pair). IMDSv2 with a single hop: the containers cannot fetch the EC2 role's
# credentials.
locals {
  host            = var.create_host ? 1 : 0
  use_default_vpc = var.create_host && var.subnet_id == "" ? 1 : 0
}

data "aws_ssm_parameter" "al2023" {
  count = local.host
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

data "aws_vpc" "default" {
  count   = local.use_default_vpc
  default = true
}

data "aws_subnets" "default" {
  count = local.use_default_vpc
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

data "aws_subnet" "chosen" {
  count = local.host
  id    = var.subnet_id != "" ? var.subnet_id : try(sort(data.aws_subnets.default[0].ids)[0], "")
}

resource "aws_security_group" "host" {
  count       = local.host
  name_prefix = "station-host-"
  description = "Simulated pumps host: egress only (MQTT, HTTPS)"
  vpc_id      = data.aws_subnet.chosen[0].vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

data "aws_iam_policy_document" "trust_ec2" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "host" {
  count              = local.host
  name               = "StationHost"
  assume_role_policy = data.aws_iam_policy_document.trust_ec2.json
}

resource "aws_iam_role_policy_attachment" "host_ssm" {
  count      = local.host
  role       = aws_iam_role.host[0].name
  policy_arn = "arn:${local.part}:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# What ./fleet/up.sh and the demo scripts need from the EC2
resource "aws_iam_role_policy" "host" {
  count = local.host
  name  = "demo-operator"
  role  = aws_iam_role.host[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # the PoC code and the fleet audio arrive through the bucket; publish.sh uploads artifacts
      { Effect = "Allow", Action = ["s3:ListBucket", "s3:GetBucketLocation"], Resource = aws_s3_bucket.artifacts.arn },
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject"], Resource = "${aws_s3_bucket.artifacts.arn}/*" },
      # publish.sh and deploy.sh
      {
        Effect = "Allow"
        Action = ["greengrass:CreateComponentVersion", "greengrass:DescribeComponent", "greengrass:GetComponent", "greengrass:ListComponents",
          "greengrass:ListComponentVersions", "greengrass:CreateDeployment", "greengrass:GetDeployment", "greengrass:ListDeployments",
          "greengrass:CancelDeployment", "greengrass:ListCoreDevices", "greengrass:GetCoreDevice", "greengrass:ListEffectiveDeployments",
        "greengrass:ListInstalledComponents"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["iot:CancelJob", "iot:CreateJob", "iot:DeleteThingShadow", "iot:DescribeJob", "iot:DescribeThing", "iot:DescribeThingGroup",
        "iot:GetThingShadow", "iot:UpdateJob", "iot:UpdateThingShadow", "iot:ListThingsInThingGroup"]
        Resource = "${local.iot_arn}:*"
      },
      { Effect = "Allow", Action = "iot:DescribeEndpoint", Resource = "*" },
      # the pumps' identity, the endpoints and the last good version
      { Effect = "Allow", Action = ["ssm:GetParameter", "ssm:GetParameters", "ssm:PutParameter"], Resource = "arn:${local.part}:ssm:${var.region}:${local.account}:parameter/station/*" },
      {
        Effect    = "Allow"
        Action    = "kms:Decrypt"
        Resource  = "*"
        Condition = { StringEquals = { "kms:ViaService" = "ssm.${var.region}.amazonaws.com" } }
      },
      # watch.sh
      { Effect = "Allow", Action = ["logs:FilterLogEvents", "logs:GetLogEvents", "logs:DescribeLogStreams", "logs:StartLiveTail", "logs:StopLiveTail"], Resource = ["${aws_cloudwatch_log_group.events.arn}", "${aws_cloudwatch_log_group.events.arn}:*"] },
      { Effect = "Allow", Action = ["logs:DescribeLogGroups", "cloudwatch:DescribeAlarms", "cloudwatch:GetMetricData"], Resource = "*" }
    ]
  })
}

resource "aws_iam_instance_profile" "host" {
  count = local.host
  name  = "StationHost"
  role  = aws_iam_role.host[0].name
}

resource "aws_instance" "host" {
  count                       = local.host
  ami                         = nonsensitive(data.aws_ssm_parameter.al2023[0].value)
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnet.chosen[0].id
  vpc_security_group_ids      = [aws_security_group.host[0].id]
  iam_instance_profile        = aws_iam_instance_profile.host[0].name
  associate_public_ip_address = true # internet egress without NAT (default VPC)

  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_size = var.disk_gb
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = templatefile("${path.module}/host-user-data.sh.tftpl", {
    region = var.region
    bucket = aws_s3_bucket.artifacts.bucket
  })
  user_data_replace_on_change = true

  tags = {
    Name = "station-host"
  }

  lifecycle {
    ignore_changes = [ami] # a new AMI must not replace the EC2 in the middle of the rehearsals
  }
}
