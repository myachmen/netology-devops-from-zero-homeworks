variable "token" {
  description = "Yandex Cloud OAuth token"
  type        = string
  sensitive   = true
}

variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
}

variable "public_zone" {
  description = "Zone for public subnet"
  type        = string
  default     = "ru-central1-a"
}

variable "private_zone_a" {
  description = "Zone for private subnet A"
  type        = string
  default     = "ru-central1-a"
}

variable "private_zone_b" {
  description = "Zone for private subnet B"
  type        = string
  default     = "ru-central1-b"
}

variable "network_name" {
  description = "VPC network name"
  type        = string
  default     = "netology-network"
}

variable "public_subnet_name" {
  description = "Public subnet name"
  type        = string
  default     = "public-subnet-a"
}

variable "private_subnet_a_name" {
  description = "Private subnet A name"
  type        = string
  default     = "private-subnet-a"
}

variable "private_subnet_b_name" {
  description = "Private subnet B name"
  type        = string
  default     = "private-subnet-b"
}
