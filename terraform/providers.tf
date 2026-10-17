terraform {
  required_version = ">= 1.15.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.238.0"
    }
  }
}

provider "yandex" {
  cloud_id  = "b1gctutkrnslve8437ea"
  folder_id = "b1gi86cp8m9talsp0tsr"
  zone      = "ru-central1-d"
}
