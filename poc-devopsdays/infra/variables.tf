variable "region" {
  description = "AWS region for the whole PoC."
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Artifacts bucket. Empty = station-<account>-<region>, the same name the scripts use."
  type        = string
  default     = ""
}

variable "force_destroy_bucket" {
  description = "true lets terraform destroy delete the bucket even when it holds artifacts."
  type        = bool
  default     = false
}

variable "pumps" {
  description = "Each pump and its ring. pump-01 is the canary (ring 0)."
  type        = map(string)
  default = {
    "pump-01" = "StationRing0"
    "pump-02" = "StationRing1"
    "pump-03" = "StationRing1"
    "pump-04" = "StationRing1"
    "pump-05" = "StationRing1"
  }

  validation {
    condition     = alltrue([for g in values(var.pumps) : contains(["StationRing0", "StationRing1"], g)])
    error_message = "Each pump goes in StationRing0 or StationRing1."
  }
}

variable "manage_identity" {
  description = <<-EOT
    true: Terraform creates the things and their certificates and stores them in Parameter Store;
    the pumps start with IDENTITY=terraform ./fleet/up.sh, with no AWS credentials in the containers.
    false: the pumps register themselves with the Greengrass installer (plain ./fleet/up.sh).
  EOT
  type        = bool
  default     = true
}

variable "alarm_threshold" {
  description = "Missed faults per minute that trigger the rollback to the last good version."
  type        = number
  default     = 8
}

variable "lambda_runtime" {
  description = "Runtime of the station-rollback Lambda."
  type        = string
  default     = "python3.12"
}

variable "log_retention_days" {
  description = "Days the events are kept in /station/events."
  type        = number
  default     = 7
}

variable "create_host" {
  description = "Creates the Linux EC2 that hosts the five pumps (Greengrass in Docker needs a Linux host)."
  type        = bool
  default     = true
}

variable "instance_type" {
  description = "EC2 instance type. Each pump is a JVM plus the model: measure memory during the rehearsal."
  type        = string
  default     = "t3.large"
}

variable "disk_gb" {
  description = "EC2 disk (image, Greengrass volumes, audio)."
  type        = number
  default     = 30
}

variable "subnet_id" {
  description = "Public subnet for the EC2. Empty = a subnet of the default VPC."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags for everything Terraform creates."
  type        = map(string)
  default = {
    project = "mlops-a-ciegas"
    talk    = "devopsdays-bogota-2026"
  }
}
