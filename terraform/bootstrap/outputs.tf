output "s3_access_key" {
  description = "S3 access key ID"
  value       = yandex_iam_service_account_static_access_key.terraform_state.access_key
  sensitive   = true
}

output "s3_secret_key" {
  description = "S3 secret access key"
  value       = yandex_iam_service_account_static_access_key.terraform_state.secret_key
  sensitive   = true
}