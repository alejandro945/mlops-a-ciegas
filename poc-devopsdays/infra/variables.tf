variable "region" {
  description = "Región de AWS de toda la PoC."
  type        = string
  default     = "us-east-1"
}

variable "nombre_bucket" {
  description = "Bucket de artefactos. Vacío = estacion-<cuenta>-<región>, el mismo nombre que usan los scripts."
  type        = string
  default     = ""
}

variable "forzar_borrado_bucket" {
  description = "true deja que terraform destroy borre el bucket aunque tenga artefactos."
  type        = bool
  default     = false
}

variable "bombas" {
  description = "Cada bomba y su anillo. bomba-01 es el canario (anillo 0)."
  type        = map(string)
  default = {
    "bomba-01" = "EstacionAnillo0"
    "bomba-02" = "EstacionAnillo1"
    "bomba-03" = "EstacionAnillo1"
    "bomba-04" = "EstacionAnillo1"
    "bomba-05" = "EstacionAnillo1"
  }

  validation {
    condition     = alltrue([for g in values(var.bombas) : contains(["EstacionAnillo0", "EstacionAnillo1"], g)])
    error_message = "Cada bomba va en EstacionAnillo0 o en EstacionAnillo1."
  }
}

variable "gestionar_identidad" {
  description = <<-EOT
    true: Terraform crea los things, sus certificados y los guarda en Parameter Store; las bombas
    arrancan con IDENTIDAD=terraform ./fleet/up.sh, sin credenciales de AWS en los contenedores.
    false: las bombas se registran solas con el instalador de Greengrass (./fleet/up.sh a secas).
  EOT
  type        = bool
  default     = true
}

variable "umbral_alarma" {
  description = "Fallas no oídas por minuto que disparan la vuelta a la última versión buena."
  type        = number
  default     = 8
}

variable "lambda_runtime" {
  description = "Runtime de la Lambda estacion-rollback."
  type        = string
  default     = "python3.12"
}

variable "retencion_logs_dias" {
  description = "Días que se guardan los eventos en /estacion/eventos."
  type        = number
  default     = 7
}

variable "crear_host" {
  description = "Crea la EC2 Linux que hospeda las cinco bombas (Greengrass en Docker pide host Linux)."
  type        = bool
  default     = true
}

variable "tipo_instancia" {
  description = "Tipo de la EC2. Cada bomba es una JVM más el modelo: mide la memoria en el ensayo."
  type        = string
  default     = "t3.large"
}

variable "disco_gb" {
  description = "Disco de la EC2 (imagen, volúmenes de Greengrass, audio)."
  type        = number
  default     = 30
}

variable "subred_id" {
  description = "Subred pública para la EC2. Vacío = una subred de la VPC por defecto."
  type        = string
  default     = ""
}

variable "cidr_ssh" {
  description = "CIDR que puede entrar por SSH (por ejemplo 203.0.113.7/32). Vacío = sin SSH; se entra con Session Manager."
  type        = string
  default     = ""
}

variable "par_de_llaves" {
  description = "Nombre de un key pair de EC2 para SSH. Vacío = sin llave."
  type        = string
  default     = ""
}

variable "etiquetas" {
  description = "Etiquetas para todo lo que crea Terraform."
  type        = map(string)
  default = {
    proyecto = "mlops-a-ciegas"
    charla   = "devopsdays-bogota-2026"
  }
}
