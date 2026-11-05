variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to the public SSH key for Kubernetes VMs"
  type        = string
  default     = "~/.ssh/yandex-diplom.pub"
}

variable "admin_cidr" {
  description = "External IPv4 CIDR allowed to access SSH and Kubernetes API"
  type        = string
}