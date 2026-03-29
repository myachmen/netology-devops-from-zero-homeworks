########################################
# Security Group: Bastion
########################################

resource "yandex_vpc_security_group" "sg_bastion" {
  name       = "sg-bastion"
  network_id = yandex_vpc_network.network.id

  ingress {
    description    = "Allow SSH from Internet"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

########################################
# Security Group: ALB
########################################

resource "yandex_vpc_security_group" "sg_alb" {
  name       = "sg-alb"
  network_id = yandex_vpc_network.network.id

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 1
    to_port        = 65535
  }

  ingress {
    description    = "Allow HTTP from Internet"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Allow HTTPS from Internet"
    protocol       = "TCP"
    port           = 443
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description       = "Allow ALB health checks"
    protocol          = "TCP"
    predefined_target = "loadbalancer_healthchecks"
    port              = 30080
  }
}

########################################
# Security Group: Web
########################################

resource "yandex_vpc_security_group" "sg_web" {
  name       = "sg-web"
  network_id = yandex_vpc_network.network.id

  ingress {
    description = "Allow HTTP from ALB"
    protocol    = "TCP"
    port        = 80

    security_group_id = yandex_vpc_security_group.sg_alb.id
  }

  ingress {
    description       = "Allow healthchecks"
    protocol          = "TCP"
    port              = 80
    predefined_target = "loadbalancer_healthchecks"
  }

  ingress {
    description = "Allow SSH from Bastion"
    protocol    = "TCP"
    port        = 22

    security_group_id = yandex_vpc_security_group.sg_bastion.id
  }

  ingress {
    description = "Allow Node Exporter from Prometheus"
    protocol    = "TCP"
    port        = 9100

    v4_cidr_blocks = ["10.10.20.0/24"]
  }

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

########################################
# Security Group: Prometheus
########################################

resource "yandex_vpc_security_group" "sg_prometheus" {
  name       = "sg-prometheus"
  network_id = yandex_vpc_network.network.id

  ingress {
    description = "Allow SSH from Bastion"
    protocol    = "TCP"
    port        = 22

    security_group_id = yandex_vpc_security_group.sg_bastion.id
  }

  ingress {
    description = "Allow Prometheus Web from Grafana"
    protocol    = "TCP"
    port        = 9090

    security_group_id = yandex_vpc_security_group.sg_grafana.id
  }

  ingress {
    description    = "Allow Prometheus Web from private network"
    protocol       = "TCP"
    port           = 9090
    v4_cidr_blocks = ["10.10.0.0/16"]
  }

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

########################################
# Security Group: Grafana
########################################

resource "yandex_vpc_security_group" "sg_grafana" {
  name       = "sg-grafana"
  network_id = yandex_vpc_network.network.id

  ingress {
    description    = "Allow Grafana Web"
    protocol       = "TCP"
    port           = 3000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH from Bastion"
    protocol    = "TCP"
    port        = 22

    security_group_id = yandex_vpc_security_group.sg_bastion.id
  }

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

#############################################
# Security Group: Elasticsearch
#############################################

resource "yandex_vpc_security_group" "sg_elasticsearch" {
  name       = "sg-elasticsearch"
  network_id = yandex_vpc_network.network.id

  ingress {
    description = "Allow SSH from Bastion"
    protocol    = "TCP"
    port        = 22

    security_group_id = yandex_vpc_security_group.sg_bastion.id
  }

  ingress {
    description = "Allow Elasticsearch from Kibana"
    protocol    = "TCP"
    port        = 9200

    security_group_id = yandex_vpc_security_group.sg_kibana.id
  }

  ingress {
    description = "Allow Filebeat from Web servers"
    protocol    = "TCP"
    port        = 9200
    v4_cidr_blocks = [
      "10.10.20.0/24",
      "10.10.30.0/24"
    ]
  }

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

#############################################
# Security Group: Kibana
#############################################

resource "yandex_vpc_security_group" "sg_kibana" {
  name       = "sg-kibana"
  network_id = yandex_vpc_network.network.id

  ingress {
    description    = "Allow Kibana Web"
    protocol       = "TCP"
    port           = 5601
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH from Bastion"
    protocol    = "TCP"
    port        = 22

    security_group_id = yandex_vpc_security_group.sg_bastion.id
  }

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}
