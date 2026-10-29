
data "yandex_compute_image" "ubuntu" {
  family    = "ubuntu-2204-lts"
  folder_id = "standard-images"
}

locals {
  k8s_nodes = {
    "k8s-control-1" = {
      zone      = "ru-central1-a"
      subnet_id = yandex_vpc_subnet.subnet_a.id
      cores     = 2
      memory    = 4
      disk_size = 30
    }

    "k8s-worker-1" = {
      zone      = "ru-central1-d"
      subnet_id = yandex_vpc_subnet.subnet_d.id
      cores     = 2
      memory    = 6
      disk_size = 50
    }

    "k8s-worker-2" = {
      zone      = "ru-central1-d"
      subnet_id = yandex_vpc_subnet.subnet_d.id
      cores     = 2
      memory    = 6
      disk_size = 50
    }
  }
}

resource "yandex_compute_instance" "k8s" {
  for_each = local.k8s_nodes

  name        = each.key
  hostname    = each.key
  zone        = each.value.zone
  platform_id = "standard-v3"

  resources {
    cores  = each.value.cores
    memory = each.value.memory
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = each.value.disk_size
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = each.value.subnet_id
    nat                = true
    nat_ip_address     = each.key == "k8s-worker-1" ? "158.160.190.231" : null
    security_group_ids = [yandex_vpc_security_group.k8s.id]
  }

  metadata = {
    user-data = templatefile("${path.module}/cloud-init.yaml.tftpl", {
      ssh_public_key = trimspace(file(pathexpand(var.ssh_public_key_path)))
    })
  }

  allow_stopping_for_update = true
}
