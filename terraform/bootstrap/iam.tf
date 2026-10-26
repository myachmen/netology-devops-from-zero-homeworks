resource "yandex_resourcemanager_folder_iam_member" "terraform_storage_admin" {
  folder_id = var.folder_id
  role      = "storage.admin"
  member    = "serviceAccount:${yandex_iam_service_account.terraform.id}"
}