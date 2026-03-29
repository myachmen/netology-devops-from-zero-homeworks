output "network_id" {
  value = yandex_vpc_network.network.id
}

output "public_subnet_a_id" {
  value = yandex_vpc_subnet.public_subnet_a.id
}

output "private_subnet_a_id" {
  value = yandex_vpc_subnet.private_subnet_a.id
}

output "private_subnet_b_id" {
  value = yandex_vpc_subnet.private_subnet_b.id
}

output "bastion_public_ip" {
  value = yandex_compute_instance.bastion.network_interface[0].nat_ip_address
}

output "web_1_private_ip" {
  value = yandex_compute_instance.web_1.network_interface[0].ip_address
}

output "web_2_private_ip" {
  value = yandex_compute_instance.web_2.network_interface[0].ip_address
}

output "web_1_id" {
  value = yandex_compute_instance.web_1.id
}

output "web_2_id" {
  value = yandex_compute_instance.web_2.id
}

output "alb_external_ip" {
  value = yandex_alb_load_balancer.web_alb.listener[0].endpoint[0].address[0].external_ipv4_address[0].address
}

output "prometheus_private_ip" {
  value = yandex_compute_instance.prometheus.network_interface[0].ip_address
}

output "grafana_public_ip" {
  value = yandex_compute_instance.grafana.network_interface[0].nat_ip_address
}

output "grafana_private_ip" {
  value = yandex_compute_instance.grafana.network_interface[0].ip_address
}

output "elasticsearch_private_ip" {
  value = yandex_compute_instance.elasticsearch.network_interface[0].ip_address
}

output "kibana_public_ip" {
  value = yandex_compute_instance.kibana.network_interface[0].nat_ip_address
}

output "kibana_private_ip" {
  value = yandex_compute_instance.kibana.network_interface[0].ip_address
}
