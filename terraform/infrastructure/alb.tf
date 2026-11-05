resource "yandex_alb_target_group" "k8s_workers" {
  name = "diplom-k8s-workers"

  target {
    subnet_id  = yandex_vpc_subnet.subnet_d.id
    ip_address = yandex_compute_instance.k8s["k8s-worker-1"].network_interface[0].ip_address
  }

  target {
    subnet_id  = yandex_vpc_subnet.subnet_d.id
    ip_address = yandex_compute_instance.k8s["k8s-worker-2"].network_interface[0].ip_address
  }
}

resource "yandex_alb_backend_group" "k8s_ingress" {
  name = "diplom-k8s-ingress"

  http_backend {
    name             = "k8s-ingress-http"
    port             = 30080
    target_group_ids = [yandex_alb_target_group.k8s_workers.id]
    weight           = 1

    load_balancing_config {
      panic_threshold = 0
    }

    healthcheck {
      timeout             = "2s"
      interval            = "5s"
      healthy_threshold   = 2
      unhealthy_threshold = 2

      http_healthcheck {
        path = "/"
      }
    }
  }
}

resource "yandex_alb_http_router" "diplom" {
  name = "diplom-http-router"
}

resource "yandex_alb_virtual_host" "diplom" {
  name           = "diplom-virtual-host"
  http_router_id = yandex_alb_http_router.diplom.id

  route {
    name = "diplom-route"

    http_route {
      http_route_action {
        backend_group_id = yandex_alb_backend_group.k8s_ingress.id
        timeout          = "60s"
      }
    }
  }
}

resource "yandex_alb_load_balancer" "diplom" {
  name               = "diplom-alb"
  network_id         = yandex_vpc_network.diplom.id
  security_group_ids = [yandex_vpc_security_group.alb.id]

  allocation_policy {
    location {
      zone_id   = "ru-central1-a"
      subnet_id = yandex_vpc_subnet.subnet_a.id
    }

    location {
      zone_id   = "ru-central1-d"
      subnet_id = yandex_vpc_subnet.subnet_d.id
    }
  }

  listener {
    name = "http-listener"

    endpoint {
      address {
        external_ipv4_address {}
      }

      ports = [80]
    }

    http {
      handler {
        http_router_id = yandex_alb_http_router.diplom.id
      }
    }
  }
}