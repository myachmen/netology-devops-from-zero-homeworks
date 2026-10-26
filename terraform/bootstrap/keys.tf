resource "yandex_iam_service_account_static_access_key" "terraform_state" {
  service_account_id = yandex_iam_service_account.terraform.id
  description        = "S3 access key for Terraform remote state"
}