# Lab 1 report (with docker from lab 2)

Lab 1 task specification: [docs/task/lab1_task.md](docs/task/lab1_task.md)
Lab 2 task specification: [docs/task/lab2_task.md](docs/task/lab2_task.md)

## Variant

N = 9 - the student's number in the group list



| Variable | Formula | Result | Meaning |
|---|---|---|---|
| V2 | (9 % 2) + 1 = 1 + 1 | 2 | Config file `/etc/mywebapp/config.yaml`; PostgreSQL database |
| V3 | (9 % 3) + 1 = 0 + 1 | 1 | Notes Service web application |
| V5 | (9 % 5) + 1 = 4 + 1 | 5 | App port 5000 |

## Web Application

### Purpose
mywebapp is an HTTP API server written in Go for managing plain-text notes. It supports content negotiation via the Accept header:
- `Accept: application/json` → returns data as a JSON response
- `Accept: text/html` → returns a plain HTML page

The application runs as a systemd service under a dedicated app system user and uses PostgreSQL as its backing store. It is exposed publicly through Nginx acting as a reverse proxy on port 80.

### Development and Testing Setup

| Tool | Notes |
|---|---|
| [Vagrant](https://developer.hashicorp.com/vagrant/downloads) | Orchestrates the VM |
|Hypervisor|[VirtualBox](https://www.virtualbox.org/wiki/Downloads) (Windows/Linux/Intel Macs) or [VMware](https://www.vmware.com/products/desktop-hypervisor/workstation-and-fusion) (Apple Silicon Macs)|
| [Git](https://git-scm.com/install) | Clone the repository |

> **Note:** Install the latest versions of those tools

#### Clone the repository

```bash
git clone https://github.com/arcctg/kpi-deployment-lab1.git
cd kpi-deployment-lab1
```

### Running the Web Application

#### With Vagrant
```bash
vagrant up
```

The application is started automatically by `vagrant up`. To manage it manually after provisioning:

```bash
# Check service status
systemctl status mywebapp.service
systemctl status mywebapp.socket

# Start / stop / restart the app (as operator or student)
sudo systemctl start mywebapp.service
sudo systemctl stop mywebapp.service
sudo systemctl restart mywebapp.service

# Reload nginx config (as operator or student)
sudo systemctl reload nginx
```

> **Note:** The `operator` user can run the above commands without a password via sudoers rules. The `student` user can run any sudo command after entering the password.

#### With Docker Compose (Lab 2)

The same stack can be run locally in containers without Vagrant.

##### Prerequisites

| Tool | Notes |
|---|---|
| [Docker](https://docs.docker.com/get-docker/) | Engine with Compose plugin |
| [Git](https://git-scm.com/install) | Clone the repository |

##### Start the stack

From the repository root:

```bash
docker compose up -d --build
```

The application is available at http://localhost:8080

Services run on a custom bridge network `mywebapp-net`. Database files are stored in the named volume `pgdata` and persist across container restarts and system reboots.

##### Stop the stack

```bash
docker compose down
```

This stops and removes containers but keeps the `pgdata` volume with database data.

##### Reset database data

```bash
docker compose down -v
```

The `-v` flag removes the `pgdata` volume. The next `docker compose up` starts with an empty database and runs migrations again.

### API Endpoint Documentation


All endpoints below are accessible through Nginx at http://localhost:8080.  
Health endpoints (`/health/*`) are blocked by Nginx and return 404 to external clients.

---

| Method | Path | Description | Accept / Content-Type | Response |
|---|---|---|---|---|
| `GET` | `/` | List of all business-logic endpoints | `text/html` only |`200 OK`|
| `GET` | `/notes` | Get all notes (returns `id`, `title`) | `text/html`or `application/json`|`200 OK`|
| `POST` | `/notes` | Create a new note (body: `title` (string, required), `content` (string, required)) | `application/x-www-form-urlencoded` or `application/json` |`201 Created`|
| `GET` | `/notes/{id}` | Get full details of a specific note (`id`, `title`, `content`, `created_at`) | `text/html` or `application/json` |`200 OK` / `404 Not Found`|
| `GET` | `/health/alive` | Liveness probe| any |`200 OK` / `404` to external clients|
| `GET` | `/health/ready` | Readiness probe | any |`200` if DB connected, `500` otherwise, `404` to external clients|

## Deployment Documentation

### Base VM Image

- **Distribution:** Debian 12 (Bookworm) — official Vagrant box [`debian/bookworm64`](https://portal.cloud.hashicorp.com/vagrant/discover/debian/bookworm64)  
> **Note:** Vagrant downloads this automatically on first `vagrant up`


### VM Resource Requirements

- **CPU**: 1 Core
- **RAM**: 1024 MB
- **Disk**: ~10 GB (dynamic, allocated by box)

### Special OS Installation Settings

No special disk partitioning or OS installation steps are required. The Vagrant box comes pre-installed with Debian 12. The provisioner script handles all further configuration automatically.

### Accessing the VM (SSH / Console)

#### `student` user
```bash
ssh student@127.0.0.1 -p 2222
# Password: 12345678
```
> **Note:** Security for `student` user wasn't stated, but I added password 12345678

####  `teacher` / `operator`
```bash
ssh teacher@127.0.0.1 -p 2222
# Password: 12345678 (must be changed on first login)

ssh operator@127.0.0.1 -p 2222
# Password: 12345678 (must be changed on first login)
```

> **Note:** The default `vagrant` user is locked after provisioning. Only `student`, `teacher`, and `operator` can log in.

### Running the Deployment Automation

The entire deployment is automated via a single Python provisioner script [`provision.py`](./provision.py) which is executed automatically by Vagrant:

```bash
vagrant up
```

To re-run provisioning on an existing VM:
```bash
vagrant provision
```

## Testing

*Detailed testing report lies in [docs/testing_report.md](/docs/testing_report.md)*

### Requirements Coverage

| Requirement | Test | Result |
|---|---|---|
| Start up goes correctly | 0 | ✅ |
| Default user locked | 1.1-1.4 | ✅ |
| `student` — admin rights, SSH login | 2.1-2.4 | ✅ |
| Gradebook file `/home/student/gradebook` = `9` | 2.5 | ✅ |
| `teacher` — admin rights, change pw on first login | 3.1-3.3 | ✅ |
| `app` — system user, nologin shell | 4.1-4.3 | ✅ |
| `operator` — limited sudo (mywebapp + nginx reload) | 5.1-5.4 | ✅ |
| All services active and enabled | 6.1-6.7 | ✅ |
| Config at `/etc/mywebapp/config.yaml` (V2=2), permissions `root:app 640` | 7.1-7.2 | ✅ |
| Systemd socket activation | 8.1-8.3 | ✅ |
| Health endpoints accessible inside VM (direct) | 9.1-9.2 | ✅ |
| Health endpoints blocked by nginx | 10.1-10.2 | ✅ |
| Root endpoint returns HTML endpoint list | 11.1 | ✅ |
| POST /notes — JSON body | 11.2 | ✅ |
| POST /notes — form-encoded body | 11.3 | ✅ |
| GET /notes — JSON and HTML (content negotiation) | 11.4-11.5 | ✅ |
| GET /notes/{id} — JSON and HTML | 11.6-11.7 | ✅ |
| API accessible from host via port forwarding | 12.1-12.2 | ✅ |
| Health blocked from host too | 12.3 | ✅ |
| DB bound to `127.0.0.1` only, inaccessible from host | 13.1-13.3 | ✅ |
| Migration script creates correct schema | 14.1-14.2 | ✅ |
| Migration is idempotent | 14.3 | ✅ |
| Nginx access log enabled | 15 | ✅ |