###web vm vars

variable "vm_web_image_family" {
  type        = string
  default     = "ubuntu-2004-lts"
  description = "Image family for web VM"
}

variable "vm_web_name" {
  type        = string
  default     = "netology-develop-platform-web"
  description = "Web VM name"
}

variable "vm_web_platform_id" {
  type        = string
  default     = "standard-v2"
  description = "Web VM platform ID"
}

/*
variable "vm_web_cores" {
  type        = number
  default     = 2
  description = "Web VM CPU cores"
}

variable "vm_web_memory" {
  type        = number
  default     = 1
  description = "Web VM RAM in GB"
}

variable "vm_web_core_fraction" {
  type        = number
  default     = 5
  description = "Web VM guaranteed CPU fraction"
}
*/

###db vm vars

variable "vm_db_name" {
  type        = string
  default     = "netology-develop-platform-db"
  description = "DB VM name"
}

variable "vm_db_platform_id" {
  type        = string
  default     = "standard-v2"
  description = "DB VM platform ID"
}

variable "vm_db_zone" {
  type        = string
  default     = "ru-central1-b"
  description = "DB VM zone"
}

variable "vm_db_cidr" {
  type        = list(string)
  default     = ["10.0.2.0/24"]
  description = "DB subnet CIDR"
}

/*
variable "vm_db_cores" {
  type        = number
  default     = 2
  description = "DB VM CPU cores"
}

# variable "vm_db_memory" {
  type        = number
  default     = 2
  description = "DB VM RAM in GB"
}

# variable "vm_db_core_fraction" {
  type        = number
  default     = 20
  description = "DB VM guaranteed CPU fraction"
}
*/

variable "vm_project_prefix" {
  type        = string
  default     = "netology"
  description = "Project prefix for VM names"
}

variable "vm_env" {
  type        = string
  default     = "develop"
  description = "Environment name"
}

variable "vm_platform_name" {
  type        = string
  default     = "platform"
  description = "Platform name part for VM names"
}

variable "vm_web_role" {
  type        = string
  default     = "web"
  description = "Web VM role"
}

variable "vm_db_role" {
  type        = string
  default     = "db"
  description = "DB VM role"
}

variable "vms_resources" {
  type = map(object({
    cores         = number
    memory        = number
    core_fraction = number
  }))

  default = {
    web = {
      cores         = 2
      memory        = 1
      core_fraction = 5
    }

    db = {
      cores         = 2
      memory        = 2
      core_fraction = 20
    }
  }

  description = "VM resources configuration"
}