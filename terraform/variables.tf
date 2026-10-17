variable "storage_access_key" {
  description = "Object Storage access key ID"
  type        = string
  sensitive   = true
}

variable "storage_secret_key" {
  description = "Object Storage secret access key"
  type        = string
  sensitive   = true
}