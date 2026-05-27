# Testing Report

All tests run after deploying the two-VM Lab 4 stack with Terraform and Ansible.

- **Host machine:** Windows, PowerShell
- **Worker VM:** `lab4-worker` — nginx, mywebapp
- **Database VM:** `lab4-db` — PostgreSQL
- **API client:** [xh](https://github.com/ducaale/xh)

> **Note:** Replace `<WORKER_IP>` and `<DB_IP>` with values from `terraform output` in the `terraform/` directory. Example values below use `192.168.56.101` and `192.168.56.102`.

---

## 0. Provisioning

Verify that infrastructure provisioning and configuration go as planned.

### 0.1 Initialize Terraform

```powershell
cd terraform
terraform init
```

**Expected output:**

```
Initializing the backend...
Initializing provider plugins...
- Finding terra-farm/virtualbox versions matching "0.2.2"...
- Installing terra-farm/virtualbox v0.2.2...
Terraform has been successfully initialized!
```

### 0.2 Create virtual machines

```powershell
terraform apply
```

**Expected output:**

```
Plan: 2 to add, 0 to change, 0 to destroy.
...
virtualbox_vm.worker: Creating...
virtualbox_vm.db: Creating...
virtualbox_vm.worker: Creation complete
virtualbox_vm.db: Creation complete

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

### 0.3 Read Terraform outputs

```powershell
terraform output
```

**Expected output:**

```
db_ip = "192.168.56.102"
db_vm_name = "lab4-db"
worker_ip = "192.168.56.101"
worker_name = "lab4-worker"
```

### 0.4 Run Ansible playbook

```powershell
cd ..\ansible
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbook.yml
```

**Expected output:**

```
PLAY [Configure all virtual machines] ******************************************
...
PLAY [Configure database server] ***********************************************
...
PLAY [Configure worker server] *************************************************
...
PLAY RECAP *********************************************************************
lab4-db                    : ok=XX   changed=XX   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
lab4-worker                : ok=XX   changed=XX   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

---

## 1. Ansible Idempotency

### 1.1 Re-run playbook without changes

```powershell
ansible-playbook playbook.yml
```

**Expected output:**

```
PLAY RECAP *********************************************************************
lab4-db                    : ok=XX   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
lab4-worker                : ok=XX   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

> **Note:** `changed=0` on both hosts confirms idempotency.

---

## 2. SSH Access

### 2.1 SSH to worker as `ansible` (key-based)

```powershell
ssh ansible@192.168.56.101
```

**Expected output:**

```
Linux lab4-worker 6.1.0-XX-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.XXX-1 x86_64
...
ansible@lab4-worker:~$
```

### 2.2 SSH to db as `ansible` (key-based)

```powershell
ssh ansible@192.168.56.102
```

**Expected output:**

```
Linux lab4-db 6.1.0-XX-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.XXX-1 x86_64
...
ansible@lab4-db:~$
```

### 2.3 SSH to worker as `teacher` (password)

```powershell
ssh teacher@192.168.56.101
# Password: 12345678
```

**Expected output:**

```
Linux lab4-worker 6.1.0-XX-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.XXX-1 x86_64
...
teacher@lab4-worker:~$
```

### 2.4 SSH to db as `teacher` (password)

```powershell
ssh teacher@192.168.56.102
# Password: 12345678
```

**Expected output:**

```
Linux lab4-db 6.1.0-XX-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.XXX-1 x86_64
...
teacher@lab4-db:~$
```

### 2.5 SSH to worker as `operator` (password)

```powershell
ssh operator@192.168.56.101
# Password: 12345678
```

**Expected output:**

```
Linux lab4-worker 6.1.0-XX-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.XXX-1 x86_64
...
operator@lab4-worker:~$
```

---

## 3. Users — Worker VM

Commands below are executed on `lab4-worker` after SSH login as `ansible`.

### 3.1 `teacher` is in `sudo` group

```bash
id teacher
```

**Expected output:**

```
uid=1001(teacher) gid=1001(teacher) groups=1001(teacher),27(sudo)
```

### 3.2 `ansible` can escalate to root without password

```bash
sudo whoami
```

**Expected output:**

```
root
```

### 3.3 `app` system user exists

```bash
id app
```

**Expected output:**

```
uid=999(app) gid=996(app) groups=996(app)
```

### 3.4 `app` shell is `nologin`

```bash
getent passwd app
```

**Expected output:**

```
app:x:999:996::/home/app:/usr/sbin/nologin
```

### 3.5 Cannot switch to `app` interactively

```bash
sudo su - app
```

**Expected output:**

```
This account is currently not available.
```

### 3.6 `operator` user exists

```bash
id operator
```

**Expected output:**

```
uid=1002(operator) gid=1002(operator) groups=1002(operator)
```

### 3.7 Operator sudoers rules

```bash
sudo cat /etc/sudoers.d/operator
```

**Expected output:**

```
operator ALL=(ALL) NOPASSWD: \
    /usr/bin/systemctl start mywebapp.socket, \
    /usr/bin/systemctl stop mywebapp.socket, \
    /usr/bin/systemctl restart mywebapp.socket, \
    /usr/bin/systemctl start mywebapp.service, \
    /usr/bin/systemctl stop mywebapp.service, \
    /usr/bin/systemctl restart mywebapp.service, \
    /usr/bin/systemctl status mywebapp.service, \
    /usr/bin/systemctl status mywebapp.socket, \
    /usr/bin/systemctl reload nginx
```

### 3.8 Allowed sudo commands for `operator`

```bash
sudo -u operator sudo -l
```

**Expected output:**

```
Matching Defaults entries for operator on lab4-worker:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, use_pty

User operator may run the following commands on lab4-worker:
    (ALL) NOPASSWD: /usr/bin/systemctl start mywebapp.socket, /usr/bin/systemctl stop mywebapp.socket,
    /usr/bin/systemctl restart mywebapp.socket, /usr/bin/systemctl start mywebapp.service,
    /usr/bin/systemctl stop mywebapp.service, /usr/bin/systemctl restart mywebapp.service,
    /usr/bin/systemctl status mywebapp.service, /usr/bin/systemctl status mywebapp.socket,
    /usr/bin/systemctl reload nginx
```

### 3.9 Gradebook file contains N=9

```bash
cat /home/student/gradebook
```

**Expected output:**

```
9
```

---

## 4. Users — DB VM

Commands below are executed on `lab4-db` after SSH login as `ansible`.

### 4.1 `teacher` exists and is in `sudo` group

```bash
id teacher
```

**Expected output:**

```
uid=1001(teacher) gid=1001(teacher) groups=1001(teacher),27(sudo)
```

### 4.2 `app` user does not exist on DB VM

```bash
id app
```

**Expected output:**

```
id: 'app': no such user
```

### 4.3 `operator` user does not exist on DB VM

```bash
id operator
```

**Expected output:**

```
id: 'operator': no such user
```

---

## 5. Service Status — Worker VM

Commands below are executed on `lab4-worker` after SSH login as `ansible`.

### 5.1 `mywebapp.service` is active

```bash
systemctl status mywebapp.service
```

**Expected output:**

```
● mywebapp.service - MyWebApp Notes Service
     Loaded: loaded (/etc/systemd/system/mywebapp.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-05-27 12:00:00 UTC; 5min ago
TriggeredBy: ● mywebapp.socket
   Main PID: 1234 (mywebapp)
      Tasks: 5 (limit: 1100)
     Memory: 8.5M
        CPU: 48ms
     CGroup: /system.slice/mywebapp.service
             └─1234 /usr/local/bin/mywebapp
```

> **Note:** "Active since" and PID will differ on your system.

### 5.2 `mywebapp.socket` is active (listening)

```bash
systemctl status mywebapp.socket
```

**Expected output:**

```
● mywebapp.socket - MyWebApp Socket
     Loaded: loaded (/etc/systemd/system/mywebapp.socket; enabled; preset: enabled)
     Active: active (running) since Wed 2026-05-27 12:00:00 UTC; 5min ago
   Triggers: ● mywebapp.service
     Listen: 127.0.0.1:5000 (Stream)
      Tasks: 0 (limit: 1100)
     Memory: 4.0K
        CPU: 674us
```

### 5.3 `nginx` is active

```bash
systemctl status nginx
```

**Expected output:**

```
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-05-27 12:00:01 UTC; 5min ago
       Docs: man:nginx(8)
    Process: 1300 ExecStartPre=/usr/sbin/nginx -t -q -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
    Process: 1301 ExecStart=/usr/sbin/nginx -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
   Main PID: 1302 (nginx)
      Tasks: 2 (limit: 1100)
     Memory: 1.8M
        CPU: 33ms
     CGroup: /system.slice/nginx.service
             ├─1302 "nginx: master process /usr/sbin/nginx -g daemon on; master_process on;"
             └─1303 "nginx: worker process"
```

### 5.4 All required services are enabled on boot

```bash
systemctl is-enabled mywebapp.socket mywebapp.service nginx
```

**Expected output:**

```
enabled
enabled
enabled
```

### 5.5 Port 5000 is bound on loopback only

```bash
ss -tlnp | grep 5000
```

**Expected output:**

```
LISTEN 0      4096       127.0.0.1:5000      0.0.0.0:*
```

---

## 6. Service Status — DB VM

Commands below are executed on `lab4-db` after SSH login as `ansible`.

### 6.1 `postgresql` is active

```bash
systemctl status postgresql
```

**Expected output:**

```
● postgresql.service - PostgreSQL RDBMS
     Loaded: loaded (/lib/systemd/system/postgresql.service; enabled; preset: enabled)
     Active: active (exited) since Wed 2026-05-27 12:00:00 UTC; 5min ago
   Main PID: 1100 (code=exited, status=0/SUCCESS)
        CPU: 4ms
```

### 6.2 `postgresql` is enabled on boot

```bash
systemctl is-enabled postgresql
```

**Expected output:**

```
enabled
```

### 6.3 UFW allows PostgreSQL from worker and SSH only

```bash
sudo ufw status
```

**Expected output:**

```
Status: active

To                         Action      From
--                         ------      ----
5432/tcp                   ALLOW       192.168.56.101
5432/tcp                   ALLOW       192.168.56.102
22/tcp                     ALLOW       Anywhere
22/tcp (v6)                ALLOW       Anywhere (v6)
```

> **Note:** The first `5432` rule allows the worker VM IP; the second allows the DB VM's own IP for local connections.

---

## 7. Configuration Files

Commands below are executed on `lab4-worker` after SSH login as `ansible`.

### 7.1 Application config points to remote database

```bash
sudo cat /etc/mywebapp/config.yaml
```

**Expected output:**

```yaml
host: 127.0.0.1
port: 5000
database:
  host: 192.168.56.102
  port: 5432
  user: mywebapp
  password: mywebapp
  dbname: mywebapp
```

> **Note:** `database.host` must match `<DB_IP>` from `terraform output`.

### 7.2 Config file ownership and permissions

```bash
ls -la /etc/mywebapp/config.yaml
```

**Expected output:**

```
-rw-r----- 1 root app 130 May 27 12:00 /etc/mywebapp/config.yaml
```

### 7.3 Socket unit file

```bash
sudo cat /etc/systemd/system/mywebapp.socket
```

**Expected output:**

```ini
[Unit]
Description=MyWebApp Socket

[Socket]
ListenStream=127.0.0.1:5000

[Install]
WantedBy=sockets.target
```

### 7.4 Service unit file

```bash
sudo cat /etc/systemd/system/mywebapp.service
```

**Expected output:**

```ini
[Unit]
Description=MyWebApp Notes Service
After=network-online.target
Wants=network-online.target
Requires=mywebapp.socket

[Service]
Type=simple
User=app
Group=app
ExecStartPre=/usr/local/bin/mywebapp -migrate
ExecStart=/usr/local/bin/mywebapp
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7.5 Nginx site configuration

```bash
sudo cat /etc/nginx/sites-available/mywebapp
```

**Expected output:**

```nginx
server {
    listen 0.0.0.0:80;
    server_name _;

    access_log /var/log/nginx/mywebapp_access.log;
    error_log  /var/log/nginx/mywebapp_error.log;

    location /health/ {
        return 404;
    }

    location = / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /notes {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        return 404;
    }
}
```

---

## 8. PostgreSQL Configuration — DB VM

Commands below are executed on `lab4-db` after SSH login as `ansible`.

### 8.1 PostgreSQL listens on VM IP

```bash
sudo grep listen_addresses /etc/postgresql/15/main/postgresql.conf
```

**Expected output:**

```
listen_addresses = '192.168.56.102'
```

> **Note:** Value must match `<DB_IP>` from `terraform output`.

### 8.2 `pg_hba.conf` allows worker and local access

```bash
sudo cat /etc/postgresql/15/main/pg_hba.conf
```

**Expected output:**

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     peer
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
host    mywebapp        mywebapp        192.168.56.101/32       scram-sha-256
host    mywebapp        mywebapp        192.168.56.102/32       scram-sha-256
```

> **Note:** Worker IP line must match `<WORKER_IP>`; DB IP line must match `<DB_IP>`.

### 8.3 PostgreSQL bound to DB VM IP only

```bash
ss -tlnp | grep 5432
```

**Expected output:**

```
LISTEN 0      244    192.168.56.102:5432      0.0.0.0:*
```

---

## 9. Health Endpoints — Direct to App

Install `xh` on the worker VM if needed: `sudo apt install -y xh`

Commands below are executed on `lab4-worker`.

### 9.1 `GET /health/alive` — always returns 200

```bash
xh GET http://127.0.0.1:5000/health/alive
```

**Expected output:**

```
HTTP/1.1 200 OK
Content-Length: 2
Content-Type: text/plain; charset=utf-8
Date: Wed, 27 May 2026 12:10:00 GMT

OK
```

### 9.2 `GET /health/ready` — returns 200 when DB is connected

```bash
xh GET http://127.0.0.1:5000/health/ready
```

**Expected output:**

```
HTTP/1.1 200 OK
Content-Length: 2
Content-Type: text/plain; charset=utf-8
Date: Wed, 27 May 2026 12:10:05 GMT

OK
```

> **Note:** This confirms the worker VM can reach PostgreSQL on the DB VM.

---

## 10. Health Endpoints — Blocked by Nginx

Commands below are executed from the Windows host.

### 10.1 `GET /health/alive` via nginx — blocked

```powershell
xh GET http://192.168.56.101/health/alive
```

**Expected output:**

```
HTTP/1.1 404 Not Found
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html
Date: Wed, 27 May 2026 12:11:00 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx/1.22.1</center>
</body>
</html>
```

### 10.2 `GET /health/ready` via nginx — blocked

```powershell
xh GET http://192.168.56.101/health/ready
```

**Expected output:**

```
HTTP/1.1 404 Not Found
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html
Date: Wed, 27 May 2026 12:11:05 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx/1.22.1</center>
</body>
</html>
```

---

## 11. API — Business Endpoints via Nginx (from Host)

Commands below are executed from the Windows host using `xh`.

### 11.1 `GET /` — Root endpoint returns HTML list of endpoints

```powershell
xh GET http://192.168.56.101/ Accept:text/html
```

**Expected output:**

```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html; charset=utf-8
Date: Wed, 27 May 2026 12:12:00 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<!DOCTYPE html><html><body><h1>Notes Service</h1><ul><li>GET /notes — list all notes</li><li>POST /notes — create note (title, content)</li><li>GET /notes/{id} — get note by id</li></ul></body></html>
```

### 11.2 `POST /notes` — Create note with form fields

```powershell
xh POST http://192.168.56.101/notes title='Test Note' content='Automated deployment is complete.'
```

**Expected output:**

```
HTTP/1.1 201 Created
Connection: keep-alive
Content-Length: 118
Content-Type: text/plain; charset=utf-8
Date: Wed, 27 May 2026 12:12:30 GMT
Server: nginx/1.22.1

{
    "id": 1,
    "title": "Test Note",
    "content": "Automated deployment is complete.",
    "created_at": "2026-05-27T12:12:30.970326Z"
}
```

### 11.3 `POST /notes` — Create note with form-encoded body

```powershell
xh --form POST http://192.168.56.101/notes title='Form Note' content='Testing form submit'
```

**Expected output:**

```
HTTP/1.1 201 Created
Connection: keep-alive
Content-Length: 104
Content-Type: text/plain; charset=utf-8
Date: Wed, 27 May 2026 12:13:00 GMT
Server: nginx/1.22.1

{
    "id": 2,
    "title": "Form Note",
    "content": "Testing form submit",
    "created_at": "2026-05-27T12:13:00.255635Z"
}
```

### 11.4 `GET /notes` — List all notes (JSON)

```powershell
xh GET http://192.168.56.101/notes Accept:application/json
```

**Expected output:**

```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 118
Content-Type: application/json
Date: Wed, 27 May 2026 12:13:30 GMT
Server: nginx/1.22.1

[
    {
        "ID": 1,
        "Title": "Test Note"
    },
    {
        "ID": 2,
        "Title": "Form Note"
    }
]
```

### 11.5 `GET /notes` — List all notes (HTML table)

```powershell
xh GET http://192.168.56.101/notes Accept:text/html
```

**Expected output:**

```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html; charset=utf-8
Date: Wed, 27 May 2026 12:14:00 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<!DOCTYPE html><html><body><h1>Notes</h1><table border="1"><tr><th>ID</th><th>Title</th></tr><tr><td>1</td><td>Test Note</td></tr><tr><td>2</td><td>Form Note</td></tr></table></body></html>
```

### 11.6 `GET /notes/1` — Get single note (JSON)

```powershell
xh GET http://192.168.56.101/notes/1 Accept:application/json
```

**Expected output:**

```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 118
Content-Type: application/json
Date: Wed, 27 May 2026 12:14:30 GMT
Server: nginx/1.22.1

{
    "id": 1,
    "title": "Test Note",
    "content": "Automated deployment is complete.",
    "created_at": "2026-05-27T12:12:30.970326Z"
}
```

### 11.7 `GET /notes/1` — Get single note (HTML)

```powershell
xh GET http://192.168.56.101/notes/1 Accept:text/html
```

**Expected output:**

```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html; charset=utf-8
Date: Wed, 27 May 2026 12:15:00 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<!DOCTYPE html><html><body><h1>Note #1</h1><p><strong>Title:</strong> Test Note</p><p><strong>Created:</strong> 2026-05-27T12:12:30Z</p><p><strong>Content:</strong><br>Automated deployment is complete.</p></body></html>
```

---

## 12. Database Access Restricted

### 12.1 Worker VM can connect to PostgreSQL on DB VM

Executed on `lab4-worker`:

```bash
PGPASSWORD=mywebapp psql -h 192.168.56.102 -U mywebapp -d mywebapp -c '\dt'
```

**Expected output:**

```
         List of relations
 Schema | Name  | Type  |  Owner
--------+-------+-------+----------
 public | notes | table | mywebapp
(1 row)
```

### 12.2 PostgreSQL is inaccessible from host machine

Executed from Windows host:

```powershell
xh GET http://192.168.56.102:5432/
```

**Expected output:**

```
xh: error: error sending request for url (http://192.168.56.102:5432/)
Caused by:
    0: client error (Connect)
    1: tcp connect error
    2: No connection could be made because the target machine actively refused it. (os error 10061)
```

> **Note:** UFW on the DB VM blocks connections from the host. PostgreSQL is only reachable from the worker VM and the DB VM itself.

### 12.3 Table schema on DB VM

Executed on `lab4-db`:

```bash
sudo -u postgres psql -d mywebapp -c '\d notes'
```

**Expected output:**

```
                                       Table "public.notes"
   Column   |           Type           | Collation | Nullable |              Default
------------+--------------------------+-----------+----------+-----------------------------------
 id         | integer                  |           | not null | nextval('notes_id_seq'::regclass)
 title      | text                     |           | not null |
 content    | text                     |           | not null |
 created_at | timestamp with time zone |           | not null | now()
Indexes:
    "notes_pkey" PRIMARY KEY, btree (id)
```

### 12.4 Migration is idempotent

Executed on `lab4-worker`:

```bash
sudo -u app /usr/local/bin/mywebapp -migrate
```

**Expected output:**

```
2026/05/27 12:16:00 migration done
```

> **Note:** Running migration on an already-migrated database succeeds without errors, because `CREATE TABLE IF NOT EXISTS` is used.

---

## 13. Nginx Access Log

Executed on `lab4-worker`:

```bash
sudo tail -10 /var/log/nginx/mywebapp_access.log
```

**Expected output:**

```
192.168.56.1 - - [27/May/2026:12:11:00 +0000] "GET /health/alive HTTP/1.1" 404 125 "-" "xh/0.25.3"
192.168.56.1 - - [27/May/2026:12:11:05 +0000] "GET /health/ready HTTP/1.1" 404 125 "-" "xh/0.25.3"
192.168.56.1 - - [27/May/2026:12:12:00 +0000] "GET / HTTP/1.1" 200 173 "-" "xh/0.25.3"
192.168.56.1 - - [27/May/2026:12:12:30 +0000] "POST /notes HTTP/1.1" 201 118 "-" "xh/0.25.3"
192.168.56.1 - - [27/May/2026:12:13:00 +0000] "POST /notes HTTP/1.1" 201 104 "-" "xh/0.25.3"
192.168.56.1 - - [27/May/2026:12:13:30 +0000] "GET /notes HTTP/1.1" 200 118 "-" "xh/0.25.3"
192.168.56.1 - - [27/May/2026:12:14:00 +0000] "GET /notes HTTP/1.1" 200 158 "-" "xh/0.25.3"
192.168.56.1 - - [27/May/2026:12:14:30 +0000] "GET /notes/1 HTTP/1.1" 200 118 "-" "xh/0.25.3"
192.168.56.1 - - [27/May/2026:12:15:00 +0000] "GET /notes/1 HTTP/1.1" 200 179 "-" "xh/0.25.3"
```

> **Note:** `192.168.56.1` is the host machine IP as seen from the worker VM on the VirtualBox host-only network.
