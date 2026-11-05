output "k8s_nodes" {
  description = "Kubernetes nodes IP addresses"

  value = {
    for name, vm in yandex_compute_instance.k8s :
    name => {
      internal_ip = vm.network_interface[0].ip_address
      external_ip = vm.network_interface[0].nat_ip_address
    }
  }
}
