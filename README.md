# Lab 4 report

Lab 4 task specification: [docs/task/lab4_task.md](docs/task/lab4_task.md)  
Lab 1 task specification (base application): [docs/task/lab1_task.md](docs/task/lab1_task.md)

## Variant

N = 9 - the student's number in the group list

| Variable | Formula | Result | Meaning |
|---|---|---|---|
| V2 | (9 % 2) + 1 = 1 + 1 | 2 | Config file `/etc/mywebapp/config.yaml`; PostgreSQL database |
| V3 | (9 % 3) + 1 = 0 + 1 | 1 | Notes Service web application |
| V5 | (9 % 5) + 1 = 4 + 1 | 5 | App port 5000 |

## Architecture

```
          +-------------- VM1 (worker) ---------------+    +--- VM2 (db) ---+
client -> | nginx (reverse proxy) -> web application  | -> | SQL database   |
          +-------------------------------------------+    +----------------+
```

| Component | Address | Port |
|---|---|---|
| nginx | 0.0.0.0 | 80 |
| web app | 127.0.0.1 | 5000 |
| PostgreSQL | VM IP (db) | 5432 |

Two Debian 12 VMs on a libvirt NAT network (`lab4-network`, `192.168.150.0/24`):

- lab4-worker: nginx, mywebapp
- lab4-db: PostgreSQL with UFW firewall

VM IPs are assigned dynamically by libvirt DHCP. Read them from `terraform output`.

## Technical challenges

The lab was initially attempted on Windows + VirtualBox, but this setup was abandoned due to critical limitations: the provider cannot natively mount official `qcow2` cloud images, silently ignores `cloud-init` configuration (breaking automated SSH/user setup), and constantly times out waiting for IP addresses because it relies on pre-installed Guest Additions.

After moving to Ubuntu 24.04 + libvirt/KVM, issues remained: QEMU disk permissions, no DHCP leases on the `default` network, and Terraform timeouts waiting for VM IPs.

The working setup uses a dedicated `lab4-network` NAT (`192.168.150.0/24`), disk clones via `base_volume_id`, a single `cloud_init.cfg` without custom `network_config`, and `dmacvicar/libvirt` v0.7.1.

## Web Application

### Purpose

mywebapp is an HTTP API server written in Go for managing plain-text notes. It supports content negotiation via the `Accept` header:

- `Accept: application/json` → JSON response
- `Accept: text/html` → plain HTML page

The application runs as a systemd service under the `app` system user and connects to PostgreSQL on the DB VM. It is exposed publicly through nginx acting as a reverse proxy on port 80.

### API Endpoint Documentation

All business endpoints are accessible through nginx at `http://<WORKER_IP>/`.  
Health endpoints (`/health/*`) are blocked by nginx and return 404 to external clients.

| Method | Path | Description | Accept / Content-Type | Response |
|---|---|---|---|---|
| `GET` | `/` | List of all business-logic endpoints | `text/html` only | `200 OK` |
| `GET` | `/notes` | Get all notes (returns `id`, `title`) | `text/html` or `application/json` | `200 OK` |
| `POST` | `/notes` | Create a new note (`title`, `content`) | `application/x-www-form-urlencoded` or JSON | `201 Created` |
| `GET` | `/notes/{id}` | Get full note details | `text/html` or `application/json` | `200 OK` / `404 Not Found` |
| `GET` | `/health/alive` | Liveness probe | any | `200 OK` (direct to app only) |
| `GET` | `/health/ready` | Readiness probe (checks DB connection) | any | `200 OK` if DB connected (direct to app only) |

## Prerequisites

| Tool | Notes |
|---|---|
| [libvirt](https://libvirt.org/) + [KVM/QEMU](https://www.qemu.org/) | Hypervisor for two VMs |
| [Terraform](https://developer.hashicorp.com/terraform/install) | >= 1.3.0 |
| [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) | Configuration management |
| [Git](https://git-scm.com/install) | Clone the repository |
| [xh](https://github.com/ducaale/xh) | HTTP client for API testing |
| SSH key pair | Used by cloud-init for the `ansible` user |

Image source: [Debian 12 cloud image (qcow2)](https://cloud.debian.org/images/cloud/bookworm/latest/)

Host setup:

```bash
# Add your user to the libvirt group (log out and back in afterwards)
sudo usermod -aG libvirt $USER

# Generate SSH key if needed
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
```

## Deployment

### 1. Clone the repository

```bash
git clone https://github.com/arcctg/kpi-deployment-lab4.git
cd kpi-deployment-lab4
```

### 2. Configure Terraform variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`

### 3. Provision infrastructure (Terraform)

```bash
terraform init
terraform apply
terraform output
```

Save the output values. You will need `<WORKER_IP>` and `<DB_IP>` for testing.

### 4. Configure services (Ansible)

```bash
cd ../ansible
chmod +x inventory.py
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbook.yml
```

Re-run to verify idempotency:

```bash
ansible-playbook playbook.yml
```

Expected: `changed=0` on both hosts (minor user-module drift may report `changed=1` on some runs).

### 5. Tear down

```bash
cd ../terraform
terraform destroy
```

## Accessing the VMs

Replace `<WORKER_IP>` / `<DB_IP>` with values from `terraform output`.

### `ansible` user (SSH key, passwordless sudo)

```bash
ssh ansible@<WORKER_IP>
ssh ansible@<DB_IP>
```

### `teacher` user (password: `12345678`, sudo with password)

```bash
ssh teacher@<WORKER_IP>
ssh teacher@<DB_IP>
```

### `operator` user (worker VM only, password: `12345678`)

```bash
ssh operator@<WORKER_IP>
```

The `operator` user can manage mywebapp and reload nginx via passwordless sudo. See [docs/testing_report.md](docs/testing_report.md) section 3.7 for allowed commands.

## Testing

Detailed testing report: [docs/testing_report.md](docs/testing_report.md)

### Requirements Coverage

| Requirement | Test | Result |
|---|---|---|
| Terraform creates 2 VMs | 0.1-0.3 | ✅ |
| Ansible configures both VMs | 0.4 | ✅ |
| Ansible idempotency (`changed=0`) | 1.1 | ✅ |
| SSH access for ansible, teacher, operator | 2.1-2.5 | ✅ |
| Users on worker VM (teacher, app, operator, gradebook) | 3.1-3.9 | ✅ |
| Users on DB VM (teacher only) | 4.1-4.3 | ✅ |
| Services active on worker (mywebapp, nginx) | 5.1-5.5 | ✅ |
| PostgreSQL active on DB VM with UFW | 6.1-6.3 | ✅ |
| Config files with dynamic DB IP | 7.1-7.5 | ✅ |
| PostgreSQL listens on DB VM IP, restricted access | 8.1-8.3 | ✅ |
| Health endpoints accessible inside worker VM | 9.1-9.2 | ✅ |
| Health endpoints blocked by nginx | 10.1-10.2 | ✅ |
| API via nginx from host (CRUD, content negotiation) | 11.1-11.7 | ✅ |
| DB accessible from worker, blocked from host | 12.1-12.4 | ✅ |
| Nginx access log enabled | 13.1 | ✅ |
