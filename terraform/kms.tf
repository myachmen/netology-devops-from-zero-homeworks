resource "yandex_kms_symmetric_key" "homework" {
  name              = "netology-security-key"
  description       = "KMS key for Netology homework 15.3"
  default_algorithm = "AES_256"
  rotation_period   = "8760h"
}

resource "yandex_kms_symmetric_key_iam_binding" "storage_encryption" {
  symmetric_key_id = yandex_kms_symmetric_key.homework.id
  role             = "kms.keys.encrypterDecrypter"

  members = [
    "serviceAccount:ajeuf0tkomoqla52cfn3"
  ]
}

