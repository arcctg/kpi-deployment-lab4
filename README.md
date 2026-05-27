# Lab 4 — IaC with Terraform and Ansible

Lab 4 task specification: [docs/task/lab4_task.md](docs/task/lab4_task.md)  
Lab 1 task specification (base application): [docs/task/lab1_task.md](docs/task/lab1_task.md)

## Variant

N = 9 — the student's number in the group list

| Variable | Formula | Result | Meaning |
|---|---|---|---|
| V2 | (9 % 2) + 1 = 1 + 1 | 2 | Config file `/etc/mywebapp/config.yaml`; PostgreSQL database |
| V3 | (9 % 3) + 1 = 0 + 1 | 1 | Notes Service web application |
| V5 | (9 % 5) + 1 = 4 + 1 | 5 | App port 5000 |

## Architecture

```
          +-------------- VM1 (worker) ---------------+    +--- VM2 (db) ---+
client -> | nginx (reverse proxy) -> web application | -> | SQL database   |
          +-------------------------------------------+    +----------------+
```

| Component | Address | Port |
|---|---|---|
| nginx | 0.0.0.0 | 80 |
| web app | 127.0.0.1 | 5000 |
| PostgreSQL | VM IP (db) | 5432 |

Two Debian 12 VMs on a VirtualBox host-only network:

- **lab4-worker** — nginx, mywebapp (Go Notes Service)
- **lab4-db** — PostgreSQL with UFW firewall

VM IPs are assigned dynamically by VirtualBox DHCP. Read them from `terraform output`.

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
| [VirtualBox](https://www.virtualbox.org/wiki/Downloads) | Hypervisor for two VMs |
| [Terraform](https://developer.hashicorp.com/terraform/install) | >= 1.3.0 |
| [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) | Configuration management |
| [Git](https://git-scm.com/install) | Clone the repository |
| SSH key pair | Used by cloud-init for the `ansible` user |
| [xh](https://github.com/ducaale/xh) | HTTP client for API testing |

Debian 12 cloud image (qcow2):

```
D:\Program Files\terraform\images\debian-12-genericcloud-amd64.qcow2
```

> **Note:** Install the latest versions of the tools above.

## Deployment

### 1. Clone the repository

```powershell
git clone https://github.com/<your-username>/kpi-deployment-lab4.git
cd kpi-deployment-lab4
```

### 2. Configure Terraform variables

```powershell
cd terraform
Copy-Item terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
debian_image         = "D:/Program Files/terraform/images/debian-12-genericcloud-amd64.qcow2"
ssh_public_key_path  = "C:/Users/<you>/.ssh/id_rsa.pub"
hostonly_interface   = "vboxnet0"
worker_name          = "lab4-worker"
db_name              = "lab4-db"
vm_cpus              = 1
vm_memory            = 1024
```

> **Note:** Ensure VirtualBox host-only adapter `vboxnet0` exists (VirtualBox → File → Host Network Manager).

### 3. Provision infrastructure (Terraform)

```powershell
terraform init
terraform apply
terraform output
```

Save the output values — you will need `<WORKER_IP>` and `<DB_IP>` for testing.

### 4. Configure services (Ansible)

```powershell
cd ..\ansible
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbook.yml
```

Re-run to verify idempotency:

```powershell
ansible-playbook playbook.yml
```

Expected: `changed=0` on both hosts.

### 5. Tear down

```powershell
cd ..\terraform
terraform destroy
```

## Accessing the VMs

Replace `<WORKER_IP>` / `<DB_IP>` with values from `terraform output`.

### `ansible` user (SSH key, passwordless sudo)

```powershell
ssh ansible@<WORKER_IP>
ssh ansible@<DB_IP>
```

### `teacher` user (password: `12345678`, sudo with password)

```powershell
ssh teacher@<WORKER_IP>
ssh teacher@<DB_IP>
```

### `operator` user (worker VM only, password: `12345678`)

```powershell
ssh operator@<WORKER_IP>
```

The `operator` user can manage mywebapp and reload nginx via passwordless sudo. See [docs/testing_report.md](docs/testing_report.md) section 3.7 for allowed commands.

## Testing the API

From the Windows host using `xh`:

```powershell
# Root endpoint
xh GET http://<WORKER_IP>/ Accept:text/html

# Create a note
xh POST http://<WORKER_IP>/notes title='Test Note' content='Hello from Lab 4'

# List notes
xh GET http://<WORKER_IP>/notes Accept:application/json

# Health blocked by nginx
xh GET http://<WORKER_IP>/health/alive
```

Health endpoints work only when accessed directly on the worker VM:

```bash
ssh ansible@<WORKER_IP>
sudo apt install -y xh
xh GET http://127.0.0.1:5000/health/alive
xh GET http://127.0.0.1:5000/health/ready
```

## Testing

Detailed testing report: [docs/testing_report.md](docs/testing_report.md)

### Requirements Coverage

| Requirement | Test | Result |
|---|---|---|
| Terraform creates 2 VMs | 0.1–0.3 | ✅ |
| Ansible configures both VMs | 0.4 | ✅ |
| Ansible idempotency (`changed=0`) | 1.1 | ✅ |
| SSH access for ansible, teacher, operator | 2.1–2.5 | ✅ |
| Users on worker VM (teacher, app, operator, gradebook) | 3.1–3.9 | ✅ |
| Users on DB VM (teacher only) | 4.1–4.3 | ✅ |
| Services active on worker (mywebapp, nginx) | 5.1–5.5 | ✅ |
| PostgreSQL active on DB VM with UFW | 6.1–6.3 | ✅ |
| Config files with dynamic DB IP | 7.1–7.5 | ✅ |
| PostgreSQL listens on DB VM IP, restricted access | 8.1–8.3 | ✅ |
| Health endpoints accessible inside worker VM | 9.1–9.2 | ✅ |
| Health endpoints blocked by nginx | 10.1–10.2 | ✅ |
| API via nginx from host (CRUD, content negotiation) | 11.1–11.7 | ✅ |
| DB accessible from worker, blocked from host | 12.1–12.4 | ✅ |
| Nginx access log enabled | 13.1 | ✅ |

## Project Structure

```
├── app/                  # Go Notes Service source code
├── ansible/              # Ansible playbook, inventory, roles
│   ├── inventory.py      # Dynamic inventory from Terraform outputs
│   ├── playbook.yml
│   └── roles/            # common, db, app, nginx, users
├── deploy/               # Jinja2 templates and systemd units
├── terraform/            # Terraform configuration for 2 VMs
│   └── cloud-init/       # cloud-init configs for ansible user
└── docs/
    ├── testing_report.md
    └── task/
```

## Users in the System

| User | VMs | Purpose | Access |
|---|---|---|---|
| `ansible` | all | Automation | SSH key, passwordless sudo |
| `teacher` | all | Verification | Password `12345678`, sudo with password |
| `app` | worker | Runs mywebapp | System user, no login |
| `operator` | worker | Manages app and nginx | Password `12345678`, limited sudo |

Gradebook file: `/home/student/gradebook` contains `9`.
