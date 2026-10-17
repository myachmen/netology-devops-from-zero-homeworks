resource "yandex_vpc_network" "homework" {
  name = "netology-lb-network"
}

resource "yandex_vpc_subnet" "homework" {
  name           = "netology-lb-subnet"
  zone           = "ru-central1-d"
  network_id     = yandex_vpc_network.homework.id
  v4_cidr_blocks = ["10.10.0.0/24"]
}
