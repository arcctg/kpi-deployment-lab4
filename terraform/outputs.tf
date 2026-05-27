output "worker_ip" {
  description = "IP address of the worker VM"
  value       = libvirt_domain.vms["worker"].network_interface[0].addresses[0]
}

output "db_ip" {
  description = "IP address of the database VM"
  value       = libvirt_domain.vms["db"].network_interface[0].addresses[0]
}

output "worker_name" {
  description = "Worker VM name"
  value       = libvirt_domain.vms["worker"].name
}

output "db_vm_name" {
  description = "Database VM name"
  value       = libvirt_domain.vms["db"].name
}

output "ansible_inventory" {
  description = "Ansible dynamic inventory metadata"
  value = {
    workers = {
      hosts = [libvirt_domain.vms["worker"].name]
      vars = {
        ansible_host = libvirt_domain.vms["worker"].network_interface[0].addresses[0]
      }
    }
    db = {
      hosts = [libvirt_domain.vms["db"].name]
      vars = {
        ansible_host = libvirt_domain.vms["db"].network_interface[0].addresses[0]
      }
    }
  }
}
