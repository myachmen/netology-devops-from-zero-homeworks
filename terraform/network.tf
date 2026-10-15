# Virtual Private Cloud
resource "yandex_vpc_network" "netology" {
  name        = "netology-network"
  description = "VPC for Netology homework 15.1"
}

# Public subnet
resource "yandex_vpc_subnet" "public" {
  name           = "public"
  zone           = "ru-central1-d"
  network_id     = yandex_vpc_network.netology.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}

# Private subnet
resource "yandex_vpc_subnet" "private" {
  name           = "private"
  zone           = "ru-central1-d"
  network_id     = yandex_vpc_network.netology.id
  v4_cidr_blocks = ["192.168.20.0/24"]
  route_table_id = yandex_vpc_route_table.private.id
}
