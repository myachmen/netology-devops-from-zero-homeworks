resource "yandex_vpc_security_group" "web" {
  name       = "netology-lb-web-sg"
  network_id = yandex_vpc_network.homework.id

  ingress {
    protocol       = "TCP"
    description    = "HTTP access to web servers"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  ingress {
    protocol       = "ICMP"
    description    = "ICMP within the subnet"
    v4_cidr_blocks = ["10.10.0.0/24"]
  }

  egress {
    protocol       = "ANY"
    description    = "Outbound traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}
