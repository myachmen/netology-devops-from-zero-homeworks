terraform {
  backend "s3" {
    bucket = "netology-diplom-tfstate-myachmen"
    key    = "infrastructure/terraform.tfstate"
    region = "ru-central1"

    endpoints = {
      s3 = "https://storage.yandexcloud.net"
    }

    skip_credentials_validation = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    use_path_style              = true
  }
}