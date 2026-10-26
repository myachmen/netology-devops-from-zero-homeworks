variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "state_bucket_name" {
  description = "Unique S3 bucket name for Terraform state"
  type        = string
}