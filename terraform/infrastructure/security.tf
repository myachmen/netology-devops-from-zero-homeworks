resource "yandex_vpc_security_group" "k8s" {
  name        = "diplom-k8s-sg"
  description = "Security group for Netology Kubernetes cluster"
  network_id  = yandex_vpc_network.diplom.id

  ingress {
    protocol       = "TCP"
    description    = "SSH from administrator IP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 22
  }

  ingress {
    protocol       = "TCP"
    description    = "Kubernetes API from administrator IP"
    v4_cidr_blocks = [var.admin_cidr]
    port           = 6443
  }

  ingress {
    protocol       = "ANY"
    description    = "Internal Kubernetes cluster traffic"
    v4_cidr_blocks = ["10.10.0.0/16"]
    from_port      = 0
    to_port        = 65535
  }

  ingress {
    protocol       = "TCP"
    description    = "Public HTTP access"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  egress {
    protocol       = "ANY"
    description    = "Outbound traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}