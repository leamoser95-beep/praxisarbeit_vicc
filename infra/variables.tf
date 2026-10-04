# Eingabeparameter. Werte werden in terraform.tfvars gesetzt
# (Vorlage: terraform.tfvars.example).

variable "subscription_id" {
  description = "ID der Azure-Subscription (az account show --query id -o tsv)"
  type        = string
}

variable "location" {
  description = "Azure-Region. Bei Azure for Students sind nicht alle Regionen erlaubt."
  type        = string
  default     = "switzerlandnorth"
}

variable "project" {
  description = "Kurzname, wird in allen Ressourcennamen verwendet"
  type        = string
  default     = "autovermietung"
}

variable "container_image" {
  description = "Öffentliches Image auf Docker Hub, z.B. docker.io/<user>/autovermietung"
  type        = string
}

variable "image_tag" {
  description = "Image-Tag. Für ein Update den Commit-Tag aus der Pipeline setzen."
  type        = string
  default     = "latest"
}

variable "min_replicas" {
  description = "Minimale Anzahl App-Instanzen (1 = kein Kaltstart, 0 = maximal günstig)"
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "Maximale Anzahl App-Instanzen beim automatischen Hochskalieren"
  type        = number
  default     = 5
}

variable "db_sku" {
  description = "Leistungsstufe der PostgreSQL-Datenbank (Burstable B1ms = günstigste Stufe)"
  type        = string
  default     = "B_Standard_B1ms"
}
