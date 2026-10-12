output "region" {
  value = var.region
}

output "bucket" {
  description = "Bucket de artefactos (publish.sh) y del código y el audio que bajan a la EC2."
  value       = aws_s3_bucket.artefactos.bucket
}

output "anillos" {
  value = { for k, g in aws_iot_thing_group.anillo : k => g.arn }
}

output "bombas" {
  description = "Bombas con identidad creada por Terraform (vacío si gestionar_identidad = false)."
  value       = { for b, g in local.bombas_tf : b => g }
}

output "endpoint_datos" {
  value = data.aws_iot_endpoint.datos.endpoint_address
}

output "dashboard" {
  value = "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards/dashboard/estacion"
}

output "host_id" {
  value = var.crear_host ? aws_instance.host[0].id : null
}

output "entrar_al_host" {
  description = "Sesión en la EC2 sin SSH (necesita el plugin de Session Manager en tu laptop)."
  value       = var.crear_host ? "aws ssm start-session --region ${var.region} --target ${aws_instance.host[0].id}" : null
}

output "siguiente" {
  value = <<-EOT

    1. Desde tu laptop, sube el código y el audio de la flota:   ./infra/subir-al-host.sh
    2. Entra al host:   ${var.crear_host ? "aws ssm start-session --region ${var.region} --target ${aws_instance.host[0].id}" : "(tu host Linux)"}
    3. En el host:      sudo su - ec2-user; traer-poc; cd ~/poc-devopsdays
                        ./fleet/build.sh && ${var.gestionar_identidad ? "IDENTIDAD=terraform " : ""}./fleet/up.sh
    4. ./demo/publish.sh 1.0.0 && ./demo/deploy.sh 1.0.0 todas && ./demo/watch.sh
  EOT
}
