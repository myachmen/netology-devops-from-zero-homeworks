resource "yandex_storage_bucket" "terraform_state" {
  bucket    = var.state_bucket_name
  folder_id = var.folder_id

  versioning {
    enabled = true
  }

  anonymous_access_flags {
    read        = false
    list        = false
    config_read = false
  }

  lifecycle {
    prevent_destroy = true
  }
}