resource "yandex_vpc_security_group" "lab" {
  name       = "netology-lab-sg"
  network_id = yandex_vpc_network.netology.id

  ingress {
    protocol       = "TCP"
    description    = "SSH access"
    v4_cidr_blocks = ["5.228.80.9/32"]
    port           = 22
  }

  ingress {
    protocol       = "ANY"
    description    = "Internal lab traffic"
    v4_cidr_blocks = ["192.168.0.0/16"]
  }

  egress {
    protocol       = "ANY"
    description    = "Outbound traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}
