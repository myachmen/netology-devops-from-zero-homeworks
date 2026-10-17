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

variable "ssh_public_key_path" {
  description = "Path to the SSH public key for Instance Group VMs"
  type        = string
  default     = "~/.ssh/netology-lb-ed25519.pub"
}
