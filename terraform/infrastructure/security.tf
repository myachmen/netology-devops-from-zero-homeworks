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

  ingress {
    protocol       = "TCP"
    description    = "ALB health checks to Kubernetes Ingress NodePort"
    v4_cidr_blocks = ["198.18.235.0/24", "198.18.248.0/24"]
    port           = 30080
  }

  egress {
    protocol       = "ANY"
    description    = "Outbound traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}

resource "yandex_vpc_security_group" "alb" {
  name        = "diplom-alb-sg"
  description = "Security group for diploma Application Load Balancer"
  network_id  = yandex_vpc_network.diplom.id

  ingress {
    protocol       = "TCP"
    description    = "Public HTTP access to ALB"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }
  
  egress {
    protocol       = "ANY"
    description    = "Outbound traffic to Kubernetes backends"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}