terraform {
  required_version = ">= 1.3.0"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.7.1"
    }
  }
}

provider "libvirt" {
  uri = var.libvirt_uri
}

resource "libvirt_network" "lab4_net" {
  name      = var.network_name
  mode      = "nat"
  addresses = [var.network_cidr]
  autostart = true

  dns {
    enabled    = true
    local_only = true
  }
}

resource "libvirt_volume" "base_image" {
  name   = "debian-12-base"
  pool   = var.storage_pool_name
  source = var.base_image_path
  format = "qcow2"
}

resource "libvirt_volume" "disks" {
  for_each = {
    worker = var.worker_name
    db     = var.db_name
  }

  name           = "${each.value}.qcow2"
  pool           = var.storage_pool_name
  base_volume_id = libvirt_volume.base_image.id
  format         = "qcow2"
  size           = var.vm_disk_size
}

resource "libvirt_cloudinit_disk" "init" {
  for_each = toset([var.worker_name, var.db_name])

  name = "${each.value}-init.iso"
  user_data = templatefile("${path.module}/cloud_init.cfg", {
    hostname       = each.value
    ssh_public_key = trimspace(file(var.ssh_public_key_path))
  })
  meta_data = ""
}

resource "libvirt_domain" "vms" {
  for_each = {
    worker = { name = var.worker_name, mem = var.vm_memory, cpu = var.vm_cpus }
    db     = { name = var.db_name, mem = var.vm_memory, cpu = var.vm_cpus }
  }

  name     = each.value.name
  memory   = each.value.mem
  vcpu     = each.value.cpu
  cloudinit = libvirt_cloudinit_disk.init[each.value.name].id

  network_interface {
    network_id     = libvirt_network.lab4_net.id
    wait_for_lease = true
  }

  disk {
    volume_id = libvirt_volume.disks[each.key].id
  }

  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }
}
