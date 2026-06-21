locals {
  vm_web_name = "${var.vm_project_prefix}-${var.vm_env}-${var.vm_platform_name}-${var.vm_web_role}"
  vm_db_name  = "${var.vm_project_prefix}-${var.vm_env}-${var.vm_platform_name}-${var.vm_db_role}"
}