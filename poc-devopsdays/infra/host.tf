# ── La EC2 que hospeda las cinco bombas ──────────────────────────────
# Greengrass en Docker pide un host Linux. Se entra con Session Manager (sin puertos abiertos);
# SSH solo si das cidr_ssh y par_de_llaves. IMDSv2 con un solo salto: los contenedores no
# pueden pedir las credenciales del rol de la EC2.
locals {
  host       = var.crear_host ? 1 : 0
  vpc_por_df = var.crear_host && var.subred_id == "" ? 1 : 0
}

data "aws_ssm_parameter" "al2023" {
  count = local.host
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

data "aws_vpc" "por_defecto" {
  count   = local.vpc_por_df
  default = true
}

data "aws_subnets" "por_defecto" {
  count = local.vpc_por_df
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.por_defecto[0].id]
  }
  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

data "aws_subnet" "elegida" {
  count = local.host
  id    = var.subred_id != "" ? var.subred_id : try(sort(data.aws_subnets.por_defecto[0].ids)[0], "")
}

resource "aws_security_group" "host" {
  count       = local.host
  name_prefix = "estacion-host-"
  description = "Host de las bombas simuladas: solo salida (MQTT, HTTPS)"
  vpc_id      = data.aws_subnet.elegida[0].vpc_id

  dynamic "ingress" {
    for_each = var.cidr_ssh != "" ? [var.cidr_ssh] : []
    content {
      description = "SSH"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
    }
  }

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

data "aws_iam_policy_document" "confia_ec2" {
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
  name               = "EstacionHost"
  assume_role_policy = data.aws_iam_policy_document.confia_ec2.json
}

resource "aws_iam_role_policy_attachment" "host_ssm" {
  count      = local.host
  role       = aws_iam_role.host[0].name
  policy_arn = "arn:${local.part}:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Lo que necesitan, desde la EC2, ./fleet/up.sh y los scripts de la demo
resource "aws_iam_role_policy" "host" {
  count = local.host
  name  = "operador-de-la-demo"
  role  = aws_iam_role.host[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # el código de la PoC y el audio de la flota llegan por el bucket; publish.sh sube artefactos
      { Effect = "Allow", Action = ["s3:ListBucket", "s3:GetBucketLocation"], Resource = aws_s3_bucket.artefactos.arn },
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject"], Resource = "${aws_s3_bucket.artefactos.arn}/*" },
      # publish.sh y deploy.sh
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
        Resource = "${local.arn_iot}:*"
      },
      { Effect = "Allow", Action = "iot:DescribeEndpoint", Resource = "*" },
      # la identidad de las bombas, los endpoints y la última versión buena
      { Effect = "Allow", Action = ["ssm:GetParameter", "ssm:GetParameters", "ssm:PutParameter"], Resource = "arn:${local.part}:ssm:${var.region}:${local.cuenta}:parameter/estacion/*" },
      {
        Effect    = "Allow"
        Action    = "kms:Decrypt"
        Resource  = "*"
        Condition = { StringEquals = { "kms:ViaService" = "ssm.${var.region}.amazonaws.com" } }
      },
      # watch.sh
      { Effect = "Allow", Action = ["logs:FilterLogEvents", "logs:GetLogEvents", "logs:DescribeLogStreams", "logs:StartLiveTail", "logs:StopLiveTail"], Resource = ["${aws_cloudwatch_log_group.eventos.arn}", "${aws_cloudwatch_log_group.eventos.arn}:*"] },
      { Effect = "Allow", Action = ["logs:DescribeLogGroups", "cloudwatch:DescribeAlarms", "cloudwatch:GetMetricData"], Resource = "*" }
    ]
  })
}

resource "aws_iam_instance_profile" "host" {
  count = local.host
  name  = "EstacionHost"
  role  = aws_iam_role.host[0].name
}

resource "aws_instance" "host" {
  count                       = local.host
  ami                         = nonsensitive(data.aws_ssm_parameter.al2023[0].value)
  instance_type               = var.tipo_instancia
  subnet_id                   = data.aws_subnet.elegida[0].id
  vpc_security_group_ids      = [aws_security_group.host[0].id]
  iam_instance_profile        = aws_iam_instance_profile.host[0].name
  key_name                    = var.par_de_llaves != "" ? var.par_de_llaves : null
  associate_public_ip_address = true # salida a internet sin NAT (VPC por defecto)

  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_size = var.disco_gb
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = templatefile("${path.module}/host-user-data.sh.tftpl", {
    region = var.region
    bucket = aws_s3_bucket.artefactos.bucket
  })
  user_data_replace_on_change = true

  tags = {
    Name = "estacion-host"
  }

  lifecycle {
    ignore_changes = [ami] # una AMI nueva no debe reemplazar la EC2 a mitad de los ensayos
  }
}
