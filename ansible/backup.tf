#############################################
# Snapshot schedule for all VM boot disks
#############################################

resource "yandex_compute_snapshot_schedule" "daily_vm_backups" {
  name = "daily-vm-backups"

  schedule_policy {
    expression = "0 1 * * *"
  }

  retention_period = "168h"

  snapshot_spec {
    description = "Daily backup of diploma VMs"
    labels = {
      project = "devops-diplom"
      type    = "daily-backup"
    }
  }

  labels = {
    project = "devops-diplom"
    purpose = "backup"
  }

  disk_ids = [
    yandex_compute_instance.bastion.boot_disk[0].disk_id,
    yandex_compute_instance.web_1.boot_disk[0].disk_id,
    yandex_compute_instance.web_2.boot_disk[0].disk_id,
    yandex_compute_instance.prometheus.boot_disk[0].disk_id,
    yandex_compute_instance.grafana.boot_disk[0].disk_id,
    yandex_compute_instance.elasticsearch.boot_disk[0].disk_id,
    yandex_compute_instance.kibana.boot_disk[0].disk_id
  ]
}
