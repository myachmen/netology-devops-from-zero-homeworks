
resource "yandex_storage_bucket" "homework" {
  bucket    = "netology-myachmen-lb-20261017"
  folder_id = "b1gi86cp8m9talsp0tsr"

  access_key = var.storage_access_key
  secret_key = var.storage_secret_key

  max_size = 1073741824

  anonymous_access_flags {
    read        = true
    list        = false
    config_read = false
  }
}

resource "yandex_storage_object" "homework_image" {
  bucket = yandex_storage_bucket.homework.bucket
  key    = "mark-yachmen.png"

  source = "${path.module}/../img/mark-yachmen.png"

  access_key = var.storage_access_key
  secret_key = var.storage_secret_key

  content_type = "image/png"
  source_hash  = filemd5("${path.module}/../img/mark-yachmen.png")

  lifecycle {
    ignore_changes = [acl]
  }
}
