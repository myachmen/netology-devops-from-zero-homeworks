resource "yandex_resourcemanager_folder_iam_member" "terraform_compute_admin" {
  folder_id = var.folder_id
  role      = "compute.admin"
  member    = "serviceAccount:${yandex_iam_service_account.terraform.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "terraform_vpc_admin" {
  folder_id = var.folder_id
  role      = "vpc.admin"
  member    = "serviceAccount:${yandex_iam_service_account.terraform.id}"
}