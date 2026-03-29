data "yandex_compute_image" "ubuntu_2204" {
  family = "ubuntu-2204-lts"
}

########################################
# Bastion VM
########################################

resource "yandex_compute_instance" "bastion" {
  name        = "bastion"
  hostname    = "bastion"
  zone        = var.public_zone
  platform_id = "standard-v3"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu_2204.id
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.public_subnet_a.id
    nat       = true

    security_group_ids = [
      yandex_vpc_security_group.sg_bastion.id
    ]
  }

  metadata = {
    enable-oslogin = "false"
    user-data      = <<-EOT
      #cloud-config
      users:
        - name: yc-user
          sudo: ALL=(ALL) NOPASSWD:ALL
          shell: /bin/bash
          ssh_authorized_keys:
            - ${file("~/.ssh/id_rsa.pub")}
    EOT
  }
}

########################################
# Web-1 VM
########################################

resource "yandex_compute_instance" "web_1" {
  name        = "web-1"
  hostname    = "web-1"
  zone        = var.private_zone_a
  platform_id = "standard-v3"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu_2204.id
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.private_subnet_a.id
    nat       = false

    security_group_ids = [
      yandex_vpc_security_group.sg_web.id
    ]
  }

  metadata = {
    enable-oslogin = "false"
    user-data      = <<-EOT
      #cloud-config
      users:
        - name: yc-user
          sudo: ALL=(ALL) NOPASSWD:ALL
          shell: /bin/bash
          ssh_authorized_keys:
            - ${file("~/.ssh/id_rsa.pub")}
    EOT
  }
}

########################################
# Web-2 VM
########################################

resource "yandex_compute_instance" "web_2" {
  name        = "web-2"
  hostname    = "web-2"
  zone        = var.private_zone_b
  platform_id = "standard-v3"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu_2204.id
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.private_subnet_b.id
    nat       = false

    security_group_ids = [
      yandex_vpc_security_group.sg_web.id
    ]
  }

  metadata = {
    enable-oslogin = "false"
    user-data      = <<-EOT
      #cloud-config
      users:
        - name: yc-user
          sudo: ALL=(ALL) NOPASSWD:ALL
          shell: /bin/bash
          ssh_authorized_keys:
            - ${file("~/.ssh/id_rsa.pub")}
    EOT
  }
}

########################################
# Prometheus VM
########################################

resource "yandex_compute_instance" "prometheus" {
  name        = "prometheus"
  hostname    = "prometheus"
  zone        = var.private_zone_a
  platform_id = "standard-v3"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu_2204.id
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.private_subnet_a.id
    nat       = false

    security_group_ids = [
      yandex_vpc_security_group.sg_prometheus.id
    ]
  }

  metadata = {
    enable-oslogin = "false"
    user-data      = <<-EOT
      #cloud-config
      users:
        - name: yc-user
          sudo: ALL=(ALL) NOPASSWD:ALL
          shell: /bin/bash
          ssh_authorized_keys:
            - ${file("~/.ssh/id_rsa.pub")}
    EOT
  }
}

#############################################
# Elasticsearch VM
#############################################

resource "yandex_compute_instance" "elasticsearch" {

  name     = "elasticsearch"
  hostname = "elasticsearch"

  zone = var.private_zone_a

  platform_id = "standard-v3"

  resources {
    cores  = 2
    memory = 4
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu_2204.id
      size     = 20
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.private_subnet_a.id
    nat       = false


    security_group_ids = [
      yandex_vpc_security_group.sg_elasticsearch.id
    ]
  }

  metadata = {
    enable-oslogin = "false"

    user-data = <<-EOT
      #cloud-config
      users:
        - name: yc-user
          sudo: ALL=(ALL) NOPASSWD:ALL
          shell: /bin/bash
          ssh_authorized_keys:
            - ${file("~/.ssh/id_rsa.pub")}
    EOT
  }

}

########################################
# Grafana VM
########################################

resource "yandex_compute_instance" "grafana" {
  name        = "grafana"
  hostname    = "grafana"
  zone        = var.public_zone
  platform_id = "standard-v3"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu_2204.id
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.public_subnet_a.id
    nat       = true

    security_group_ids = [
      yandex_vpc_security_group.sg_grafana.id
    ]
  }

  metadata = {
    enable-oslogin = "false"
    user-data      = <<-EOT
      #cloud-config
      users:
        - name: yc-user
          sudo: ALL=(ALL) NOPASSWD:ALL
          shell: /bin/bash
          ssh_authorized_keys:
            - ${file("~/.ssh/id_rsa.pub")}
    EOT
  }
}

#############################################
# Kibana VM
#############################################

resource "yandex_compute_instance" "kibana" {

  name     = "kibana"
  hostname = "kibana"

  zone = var.public_zone

  platform_id = "standard-v3"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu_2204.id
      size     = 20
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.public_subnet_a.id
    nat       = true

    security_group_ids = [
      yandex_vpc_security_group.sg_kibana.id
    ]
  }

  metadata = {
    enable-oslogin = "false"

    user-data = <<-EOT
      #cloud-config
      users:
        - name: yc-user
          sudo: ALL=(ALL) NOPASSWD:ALL
          shell: /bin/bash
          ssh_authorized_keys:
            - ${file("~/.ssh/id_rsa.pub")}
    EOT
  }

}
