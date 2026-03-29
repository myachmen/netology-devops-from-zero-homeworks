resource "yandex_alb_target_group" "web_target_group" {
  name = "web-target-group"

  target {
    subnet_id  = yandex_vpc_subnet.private_subnet_a.id
    ip_address = yandex_compute_instance.web_1.network_interface[0].ip_address
  }

  target {
    subnet_id  = yandex_vpc_subnet.private_subnet_b.id
    ip_address = yandex_compute_instance.web_2.network_interface[0].ip_address
  }
}

resource "yandex_alb_backend_group" "web_backend_group" {
  name = "web-backend-group"

  http_backend {
    name             = "web-http-backend"
    port             = 80
    target_group_ids = [yandex_alb_target_group.web_target_group.id]

    load_balancing_config {
      panic_threshold = 50
    }

    healthcheck {
      timeout             = "1s"
      interval            = "2s"
      healthy_threshold   = 2
      unhealthy_threshold = 2

      http_healthcheck {
        path = "/"
      }
    }
  }
}

resource "yandex_alb_http_router" "web_http_router" {
  name = "web-http-router"
}

resource "yandex_alb_virtual_host" "web_virtual_host" {
  name           = "web-virtual-host"
  http_router_id = yandex_alb_http_router.web_http_router.id

  route {
    name = "default-route"

    http_route {
      http_route_action {
        backend_group_id = yandex_alb_backend_group.web_backend_group.id
      }
    }
  }
}

resource "yandex_alb_load_balancer" "web_alb" {
  name       = "web-alb"
  network_id = yandex_vpc_network.network.id

  security_group_ids = [
    yandex_vpc_security_group.sg_alb.id
  ]

  allocation_policy {
    location {
      zone_id   = var.public_zone
      subnet_id = yandex_vpc_subnet.public_subnet_a.id
    }
  }

  listener {
    name = "web-listener"
    endpoint {
      address {
        external_ipv4_address {}
      }
      ports = [80]
    }

    http {
      handler {
        http_router_id = yandex_alb_http_router.web_http_router.id
      }
    }
  }
}
