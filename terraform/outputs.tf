output "worker_ip" {
  description = "Host-only IP address of the worker VM"
  value       = virtualbox_vm.worker.network_adapter[0].ipv4_address
}

output "db_ip" {
  description = "Host-only IP address of the database VM"
  value       = virtualbox_vm.db.network_adapter[0].ipv4_address
}

output "worker_name" {
  description = "Worker VM name"
  value       = virtualbox_vm.worker.name
}

output "db_vm_name" {
  description = "Database VM name"
  value       = virtualbox_vm.db.name
}

output "ansible_inventory" {
  description = "Ansible dynamic inventory metadata"
  value = {
    workers = {
      hosts = [virtualbox_vm.worker.name]
      vars = {
        ansible_host = virtualbox_vm.worker.network_adapter[0].ipv4_address
      }
    }
    db = {
      hosts = [virtualbox_vm.db.name]
      vars = {
        ansible_host = virtualbox_vm.db.network_adapter[0].ipv4_address
      }
    }
  }
}
