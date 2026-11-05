resource "yandex_vpc_network" "diplom" {
  name        = "diplom-network"
  description = "VPC for Netology DevOps diploma"
}

resource "yandex_vpc_subnet" "subnet_a" {
  name           = "diplom-subnet-a"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.diplom.id
  v4_cidr_blocks = ["10.10.1.0/24"]
}

resource "yandex_vpc_subnet" "subnet_d" {
  name           = "diplom-subnet-d"
  zone           = "ru-central1-d"
  network_id     = yandex_vpc_network.diplom.id
  v4_cidr_blocks = ["10.10.2.0/24"]
}

resource "yandex_vpc_subnet" "subnet_e" {
  name           = "diplom-subnet-e"
  zone           = "ru-central1-e"
  network_id     = yandex_vpc_network.diplom.id
  v4_cidr_blocks = ["10.10.3.0/24"]
}