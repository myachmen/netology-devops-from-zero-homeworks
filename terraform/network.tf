resource "yandex_vpc_network" "network" {
  name = var.network_name
}

resource "yandex_vpc_subnet" "public_subnet_a" {
  name           = var.public_subnet_name
  zone           = var.public_zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.10.10.0/24"]
}

resource "yandex_vpc_subnet" "private_subnet_a" {
  name           = var.private_subnet_a_name
  zone           = var.private_zone_a
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.10.20.0/24"]

  route_table_id = yandex_vpc_route_table.private_route_table.id
}

resource "yandex_vpc_subnet" "private_subnet_b" {
  name           = var.private_subnet_b_name
  zone           = var.private_zone_b
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.10.30.0/24"]

  route_table_id = yandex_vpc_route_table.private_route_table.id
}

resource "yandex_vpc_gateway" "nat_gateway" {
  name = "nat-gateway"
  shared_egress_gateway {}
}

resource "yandex_vpc_route_table" "private_route_table" {
  network_id = yandex_vpc_network.network.id

  static_route {
    destination_prefix = "0.0.0.0/0"
    gateway_id         = yandex_vpc_gateway.nat_gateway.id
  }
}
