variable "debian_image" {
  description = "Path to Debian 12 cloud image (qcow2/ova) for VirtualBox provider"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key injected for the ansible user via cloud-init"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "hostonly_interface" {
  description = "VirtualBox host-only network interface name"
  type        = string
  default     = "vboxnet0"
}

variable "worker_name" {
  description = "Name of the worker VM"
  type        = string
  default     = "lab4-worker"
}

variable "db_name" {
  description = "Name of the database VM"
  type        = string
  default     = "lab4-db"
}

variable "vm_cpus" {
  description = "Number of virtual CPUs per VM"
  type        = number
  default     = 1
}

variable "vm_memory" {
  description = "Memory in MiB per VM"
  type        = number
  default     = 1024
}
