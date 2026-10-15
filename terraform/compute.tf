# NAT instance
resource "yandex_compute_instance" "nat" {
  name        = "nat-instance"
  platform_id = "standard-v3"
  zone        = "ru-central1-d"

  resources {
    cores         = 2
    memory        = 2
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = "fd80mrhj8fl2oe87o4e1"
      size     = 10
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.public.id
    ip_address         = "192.168.10.254"
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(pathexpand("~/.ssh/id_ed25519.pub"))}"
  }
}

# Public VM
resource "yandex_compute_instance" "public" {
  name        = "public-vm"
  platform_id = "standard-v3"
  zone        = "ru-central1-d"

  resources {
    cores         = 2
    memory        = 2
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.public.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(pathexpand("~/.ssh/id_ed25519.pub"))}"
  }
}

# Private VM
resource "yandex_compute_instance" "private" {
  name        = "private-vm"
  platform_id = "standard-v3"
  zone        = "ru-central1-d"

  resources {
    cores         = 2
    memory        = 2
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.private.id
    nat                = false
    security_group_ids = [yandex_vpc_security_group.lab.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(pathexpand("~/.ssh/id_ed25519.pub"))}"
  }
}
