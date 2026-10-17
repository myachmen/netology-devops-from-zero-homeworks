resource "yandex_compute_instance_group" "homework" {
  name               = "netology-lb-ig"
  folder_id          = "b1gi86cp8m9talsp0tsr"
  service_account_id = "ajeutaso4967kahusiro"

  instance_template {
    platform_id = "standard-v3"

    resources {
      cores         = 2
      memory        = 2
      core_fraction = 20
    }

    boot_disk {
      mode = "READ_WRITE"

      initialize_params {
        image_id = "fd827b91d99psvq5fjit"
        size     = 32
        type     = "network-ssd"
      }
    }

    network_interface {
      network_id         = yandex_vpc_network.homework.id
      subnet_ids         = [yandex_vpc_subnet.homework.id]
      nat                = true
      security_group_ids = [yandex_vpc_security_group.web.id]
    }

    metadata = {
      user-data = templatefile("${path.module}/cloud-init.yaml.tftpl", {
        ssh_public_key = trimspace(file(pathexpand(var.ssh_public_key_path)))
        hostname       = "netology-lb"
        image_url      = "https://storage.yandexcloud.net/${yandex_storage_bucket.homework.bucket}/${yandex_storage_object.homework_image.key}"
      })
    }
  }

  scale_policy {
    fixed_scale {
      size = 3
    }
  }

  allocation_policy {
    zones = ["ru-central1-d"]
  }

  deploy_policy {
    max_unavailable = 1
    max_expansion   = 0
    max_creating    = 3
  }

  health_check {
    interval = 30
    timeout  = 10

    http_options {
      port = 80
      path = "/"
    }
  }

  load_balancer {
    target_group_name = "netology-lb-target-group"
  }
}
