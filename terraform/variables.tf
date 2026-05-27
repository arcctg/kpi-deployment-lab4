variable "libvirt_uri" {
  description = "Libvirt connection URI"
  type        = string
  default     = "qemu:///system"
}

variable "storage_pool_name" {
  description = "Name of the libvirt storage pool for VM disks"
  type        = string
  default     = "default"
}

variable "base_image_path" {
  description = "Path to Debian 12 cloud image (qcow2) for libvirt provider"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key injected for the ansible user via cloud-init"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "network_name" {
  description = "Libvirt network name"
  type        = string
  default     = "lab4-network"
}

variable "network_cidr" {
  description = "CIDR for the libvirt NAT network"
  type        = string
  default     = "192.168.150.0/24"
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

variable "vm_disk_size" {
  description = "Disk size in bytes for each VM volume"
  type        = number
  default     = 10 * 1024 * 1024 * 1024
}
