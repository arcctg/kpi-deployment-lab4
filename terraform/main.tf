terraform {
  required_version = ">= 1.3.0"

  required_providers {
    virtualbox = {
      source  = "terra-farm/virtualbox"
      version = "0.2.2"
    }
  }
}

provider "virtualbox" {
  checksum = false
}

locals {
  cloud_init_common = {
    ssh_public_key = trimspace(file(var.ssh_public_key_path))
  }
}

resource "virtualbox_vm" "worker" {
  name   = var.worker_name
  image  = var.debian_image
  cpus   = var.vm_cpus
  memory = "${var.vm_memory} mib"

  network_adapter {
    type           = "hostonly"
    host_interface = var.hostonly_interface
  }

  user_data = templatefile("${path.module}/cloud-init/worker.cfg", merge(local.cloud_init_common, {
    hostname = var.worker_name
  }))
}

resource "virtualbox_vm" "db" {
  name   = var.db_name
  image  = var.debian_image
  cpus   = var.vm_cpus
  memory = "${var.vm_memory} mib"

  network_adapter {
    type           = "hostonly"
    host_interface = var.hostonly_interface
  }

  user_data = templatefile("${path.module}/cloud-init/db.cfg", merge(local.cloud_init_common, {
    hostname = var.db_name
  }))
}
