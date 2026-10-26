resource "yandex_iam_service_account" "terraform" {
  name        = "terraform-diplom"
  description = "Service account for Netology DevOps diploma"
  folder_id   = var.folder_id
}