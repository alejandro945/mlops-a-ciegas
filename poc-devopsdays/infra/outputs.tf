output "region" {
  value = var.region
}

output "bucket" {
  description = "Artifacts bucket (publish.sh), also used to ship the code and the fleet audio to the EC2."
  value       = aws_s3_bucket.artifacts.bucket
}

output "rings" {
  value = { for k, g in aws_iot_thing_group.ring : k => g.arn }
}

output "pumps" {
  description = "Pumps whose identity Terraform created (empty when manage_identity = false)."
  value       = { for p, g in local.tf_pumps : p => g }
}

output "data_endpoint" {
  value = data.aws_iot_endpoint.data.endpoint_address
}

output "dashboard" {
  value = "https://${var.region}.console.aws.amazon.com/cloudwatch/home?region=${var.region}#dashboards/dashboard/station"
}

output "host_id" {
  value = var.create_host ? aws_instance.host[0].id : null
}

output "connect_to_host" {
  description = "Session Manager session on the EC2 (needs the Session Manager plugin on your laptop)."
  value       = var.create_host ? "aws ssm start-session --region ${var.region} --target ${aws_instance.host[0].id}" : null
}

output "next_steps" {
  value = <<-EOT

    1. From your laptop, upload the code and the fleet audio:   ./infra/upload-to-host.sh
    2. Open a session on the host:   ${var.create_host ? "aws ssm start-session --region ${var.region} --target ${aws_instance.host[0].id}" : "(your Linux host)"}
    3. On the host:      sudo su - ec2-user; fetch-poc; cd ~/poc-devopsdays
                         ./fleet/build.sh && ${var.manage_identity ? "IDENTITY=terraform " : ""}./fleet/up.sh
    4. ./demo/publish.sh 1.0.0 && ./demo/deploy.sh 1.0.0 all && ./demo/watch.sh
  EOT
}
