# Testing Report

All tests run on a Vagrant VM `debian/bookworm64` after provisioning using `student` user or on a Windows host machine via PowerShell.

## 0. Start Up And Provisioning
Verify that provisioning goes as planned.
```
vagrant up
```
**Expected output:**
```
...
    default: ==> Installing packages
    default:     OK
    default: ==> Creating users
    default:     OK
    default: ==> Configuring SSH password auth
    default:     OK
    default: ==> Setting up PostgreSQL
    default:     OK
    default: ==> Building Go application
    default:     OK
    default: ==> Deploying application config
    default:     OK
    default: ==> Deploying systemd units
    default:     OK
    default: ==> Configuring nginx
    default:     OK
    default: ==> Deploying sudoers rules
    default:     OK
    default: ==> Creating gradebook
    default:     OK
    default: ==> Migrating SSH keys to student
    default:     OK
    default: ==> Locking vagrant user
    default:     OK
    default:
    default: ==> Provisioning complete
```


## 1. Default User `vagrant` Is Blocked

### 1.1 Login via `vagrant ssh` fails

```
vagrant ssh
```

**Expected output:**
```
Linux bookworm 6.1.0-29-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.123-1 (2025-01-02) x86_64
...
This account is currently not available.
```

> **Note:** Next are shown commands executed after logging in as a `student`, which will be shown after that

### 1.2 Cannot switch to `vagrant` user interactively

```bash
sudo su - vagrant
```

**Expected output:**
```
This account is currently not available.
```

### 1.3 Password status shows locked (`L`)

```bash
sudo passwd -S vagrant
```

**Expected output:**
```
vagrant L 2025-01-26 0 99999 7 -1
```

### 1.4 Shell is set to `nologin`

```bash
getent passwd vagrant
```

**Expected output:**
```
vagrant:x:1000:1000::/home/vagrant:/usr/sbin/nologin
```

---

## 2. Student User

### 2.1 SSH login with Vagrant private key succeeds

```
ssh student@127.0.0.1 -p 2222
```

**Expected output:**
```
The authenticity of host '[127.0.0.1]:2222 ([127.0.0.1]:2222)' can't be established.
...
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '[127.0.0.1]:2222' to the list of known hosts.
student@127.0.0.1's password:
...
student@bookworm:~$
```

### 2.2 User ID and groups

```bash
id student
```

**Expected output:**
```
uid=1001(student) gid=1001(student) groups=1001(student),27(sudo)
```

### 2.3 Current session groups

```bash
groups
```

**Expected output:**
```
student sudo
```

### 2.4 Sudo escalation to root

```bash
sudo whoami
```

**Expected output:**
```
root
```

### 2.5 Gradebook file contains N=9

```bash
cat /home/student/gradebook
```

**Expected output:**
```
9
```

## 3. Teacher User

### 3.1 User ID and groups

```bash
id teacher
```

**Expected output:**
```
uid=1002(teacher) gid=1002(teacher) groups=1002(teacher),27(sudo)
```

### 3.2 Teacher is in `sudo` group

```bash
getent group sudo
```

**Expected output:**
```
sudo:x:27:student,teacher
```

### 3.3 Password must be changed on first login

```bash
sudo chage -l teacher
```

**Expected output:**
```
Last password change                                    : password must be changed
Password expires                                        : password must be changed
Password inactive                                       : password must be changed
Account expires                                         : never
Minimum number of days between password change          : 0
Maximum number of days between password change          : 99999
Number of days of warning before password expires       : 7
```

---

## 4. App User

### 4.1 User ID

```bash
id app
```

**Expected output:**
```
uid=999(app) gid=996(app) groups=996(app)
```

### 4.2 Shell is `nologin` (system user, no interactive login)

```bash
getent passwd app
```

**Expected output:**
```
app:x:999:996::/home/app:/usr/sbin/nologin
```

### 4.3 Cannot switch to `app` user interactively

```bash
sudo su - app
```

**Expected output:**
```
This account is currently not available.
```

---

## 5. Operator User

### 5.1 User ID

```bash
id operator
```

**Expected output:**
```
uid=1003(operator) gid=37(operator) groups=37(operator)
```

### 5.2 Password must be changed on first login

```bash
sudo chage -l operator
```

**Expected output:**
```
Last password change                                    : password must be changed
Password expires                                        : password must be changed
Password inactive                                       : password must be changed
Account expires                                         : never
Minimum number of days between password change          : 0
Maximum number of days between password change          : 99999
Number of days of warning before password expires       : 7
```

### 5.3 Sudoers rules for operator

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

### 5.4 Allowed sudo commands for operator

```bash
sudo -u operator sudo -l
```

**Expected output:**
```
Matching Defaults entries for operator on bookworm:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, use_pty

User operator may run the following commands on bookworm:
    (ALL) NOPASSWD: /usr/bin/systemctl start mywebapp.socket, /usr/bin/systemctl stop mywebapp.socket,
    /usr/bin/systemctl restart mywebapp.socket, /usr/bin/systemctl start mywebapp.service,
    /usr/bin/systemctl stop mywebapp.service, /usr/bin/systemctl restart mywebapp.service,
    /usr/bin/systemctl status mywebapp.service, /usr/bin/systemctl status mywebapp.socket,
    /usr/bin/systemctl reload nginx
```

---

## 6. Service Status

### 6.1 `mywebapp.service` is active

```bash
systemctl status mywebapp.service
```

**Expected output:**
```
● mywebapp.service - MyWebApp Notes Service
     Loaded: loaded (/etc/systemd/system/mywebapp.service; enabled; preset: enabled)
     Active: active (running) since Sun 2026-05-24 15:32:17 UTC; 1h 1min ago
TriggeredBy: ● mywebapp.socket
   Main PID: 5936 (mywebapp)
      Tasks: 5 (limit: 1100)
     Memory: 8.5M
        CPU: 48ms
     CGroup: /system.slice/mywebapp.service
             └─5936 /usr/local/bin/mywebapp
```
> **Note:** "Active since" will be different here and in all other outputs

### 6.2 `mywebapp.socket` is active (listening)

```bash
systemctl status mywebapp.socket
```

**Expected output:**
```
● mywebapp.socket - MyWebApp Socket
     Loaded: loaded (/etc/systemd/system/mywebapp.socket; enabled; preset: enabled)
     Active: active (running) since Sun 2026-05-24 15:32:17 UTC; 1h 1min ago
   Triggers: ● mywebapp.service
     Listen: 127.0.0.1:5000 (Stream)
      Tasks: 0 (limit: 1100)
     Memory: 4.0K
        CPU: 674us
```

### 6.3 `nginx` is active

```bash
systemctl status nginx
```

**Expected output:**
```
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; preset: enabled)
     Active: active (running) since Sun 2026-05-24 15:32:19 UTC; 2h 3min ago
       Docs: man:nginx(8)
    Process: 6008 ExecStartPre=/usr/sbin/nginx -t -q -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
    Process: 6009 ExecStart=/usr/sbin/nginx -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
   Main PID: 6010 (nginx)
      Tasks: 2 (limit: 1100)
     Memory: 1.8M
        CPU: 33ms
     CGroup: /system.slice/nginx.service
             ├─6010 "nginx: master process /usr/sbin/nginx -g daemon on; master_process on;"
             └─6013 "nginx: worker process"
```

### 6.4 `postgresql` is active

```bash
systemctl status postgresql
```

**Expected output:**
```
● postgresql.service - PostgreSQL RDBMS
     Loaded: loaded (/lib/systemd/system/postgresql.service; enabled; preset: enabled)
     Active: active (exited) since Sun 2026-05-24 15:31:48 UTC; 2h 5min ago
   Main PID: 5386 (code=exited, status=0/SUCCESS)
        CPU: 4ms
```

### 6.5-6.7 All required services are enabled on boot

```bash
systemctl is-enabled mywebapp.socket
systemctl is-enabled mywebapp.service
systemctl is-enabled nginx
```

**Expected output:**
```
enabled
enabled
enabled
```

---

## 7. Configuration File

### 7.1 Config file contents

```bash
sudo cat /etc/mywebapp/config.yaml
```

**Expected output:**
```yaml
host: 127.0.0.1
port: 5000
database:
  host: 127.0.0.1
  port: 5432
  user: mywebapp
  password: mywebapp
  dbname: mywebapp
```

### 7.2 File ownership and permissions

```bash
ls -la /etc/mywebapp/config.yaml
```

**Expected output:**
```
-rw-r----- 1 root app 125 May 24 15:32 /etc/mywebapp/config.yaml
```

> **Note:** Owner: `root`, group: `app`, permissions: `640` — only root can write, app user can read, others cannot access.

---

## 8. Systemd Socket Activation

### 8.1 Socket unit file

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

### 8.2 Service unit file

```bash
sudo cat /etc/systemd/system/mywebapp.service
```

**Expected output:**
```ini
[Unit]
Description=MyWebApp Notes Service
After=network.target postgresql.service
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

### 8.3 Port 5000 is bound on loopback only

```bash
ss -tlnp | grep 5000
```

**Expected output:**
```
LISTEN 0      4096       127.0.0.1:5000      0.0.0.0:*
```

---

## 9. API — Health Endpoints (Inside VM, Direct to App)

Requests go directly to the app on `127.0.0.1:5000`, bypassing nginx.

### 9.1 `GET /health/alive` — always returns 200

```bash
xh GET http://127.0.0.1:5000/health/alive
```

**Expected output:**
```
HTTP/1.1 200 OK
Content-Length: 2
Content-Type: text/plain; charset=utf-8
Date: Sun, 24 May 2026 17:41:25 GMT

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
Date: Sun, 24 May 2026 17:43:28 GMT

OK
```

---

## 10. API — Health Endpoints Blocked by Nginx (Inside VM)

Same endpoints accessed through nginx on port 80 — must return 404.

### 10.1 `GET /health/alive` via nginx — blocked

```bash
xh GET http://localhost/health/alive
```

**Expected output:**
```
HTTP/1.1 404 Not Found
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html
Date: Sun, 24 May 2026 17:44:05 GMT
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

```bash
xh GET http://localhost/health/ready
```

**Expected output:**
```
HTTP/1.1 404 Not Found
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html
Date: Sun, 24 May 2026 17:44:39 GMT
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

## 11. API — Business Endpoints via Nginx (Inside VM)

### 11.1 `GET /` — Root endpoint returns HTML list of endpoints

```bash
xh GET http://localhost/ Accept:text/html
```

**Expected output:**
```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html; charset=utf-8
Date: Sun, 24 May 2026 17:45:23 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<!DOCTYPE html><html><body><h1>Notes Service</h1><ul><li>GET /notes — list all notes</li><li>POST /notes — create note (title, content)</li><li>GET /notes/{id} — get note by id</li></ul></body></html>
```

### 11.2 `POST /notes` — Create note with JSON body

```bash
xh POST http://localhost/notes title='Test Note' content='Automated deployment is complete.'
```

**Expected output:**
```
HTTP/1.1 201 Created
Connection: keep-alive
Content-Length: 118
Content-Type: text/plain; charset=utf-8
Date: Sun, 24 May 2026 17:46:21 GMT
Server: nginx/1.22.1

{
    "id": 1,
    "title": "Test Note",
    "content": "Automated deployment is complete.",
    "created_at": "2026-05-24T17:46:21.970326Z"
}
```

### 11.3 `POST /notes` — Create note with form-encoded body

```bash
xh --form POST http://localhost/notes title='Form Note' content='Testing form submit'
```

**Expected output:**
```
HTTP/1.1 201 Created
Connection: keep-alive
Content-Length: 104
Content-Type: text/plain; charset=utf-8
Date: Sun, 24 May 2026 18:07:37 GMT
Server: nginx/1.22.1

{
    "id": 2,
    "title": "Form Note",
    "content": "Testing form submit",
    "created_at": "2026-05-24T18:07:37.255635Z"
}
```

### 11.4 `GET /notes` — List all notes (JSON)

```bash
xh GET http://localhost/notes Accept:application/json
```

**Expected output:**
```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 118
Content-Type: application/json
Date: Sun, 24 May 2026 18:07:56 GMT
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

```bash
xh GET http://localhost/notes Accept:text/html
```

**Expected output:**
```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html; charset=utf-8
Date: Sun, 24 May 2026 18:09:02 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<!DOCTYPE html><html><body><h1>Notes</h1><table border="1"><tr><th>ID</th><th>Title</th></tr><tr><td>1</td><td>Test Note</td></tr><tr><td>2</td><td>Form Note</td></tr></table></body></html>
```

### 11.6 `GET /notes/1` — Get single note (JSON)

```bash
xh GET http://localhost/notes/1 Accept:application/json
```

**Expected output:**
```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 118
Content-Type: application/json
Date: Sun, 24 May 2026 18:11:55 GMT
Server: nginx/1.22.1

{
    "id": 1,
    "title": "Test Note",
    "content": "Automated deployment is complete.",
    "created_at": "2026-05-24T17:46:21.970326Z"
}
```

### 11.7 `GET /notes/1` — Get single note (HTML)

```bash
xh GET http://localhost/notes/1 Accept:text/html
```

**Expected output:**
```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html; charset=utf-8
Date: Sun, 24 May 2026 18:12:34 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<!DOCTYPE html><html><body><h1>Note #1</h1><p><strong>Title:</strong> Test Note</p><p><strong>Created:</strong> 2026-05-24T17:46:21Z</p><p><strong>Content:</strong><br>Automated deployment is complete.</p></body></html>
```

---

## 12. API — From Host Machine (Outside VM)

Requests from Windows host via Vagrant port forwarding (`localhost:8080` → VM port 80 → nginx → app).

### 12.1 `GET /` — Root endpoint from host

```powershell
xh GET http://localhost:8080/ Accept:text/html
```

**Expected output:**
```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html; charset=utf-8
Date: Sun, 24 May 2026 18:13:58 GMT
Server: nginx/1.22.1
Transfer-Encoding: chunked

<!DOCTYPE html><html><body><h1>Notes Service</h1><ul><li>GET /notes — list all notes</li><li>POST /notes — create note (title, content)</li><li>GET /notes/{id} — get note by id</li></ul></body></html>
```

### 12.2 `GET /notes` — List notes from host (JSON)

```powershell
xh GET http://localhost:8080/notes Accept:application/json
```

**Expected output:**
```
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 118
Content-Type: application/json
Date: Sun, 24 May 2026 18:14:49 GMT
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

### 12.3 `GET /health/alive` — Blocked from host too

```powershell
xh GET http://localhost:8080/health/alive
```

**Expected output:**
```
HTTP/1.1 404 Not Found
Connection: keep-alive
Content-Encoding: gzip
Content-Type: text/html
Date: Sun, 24 May 2026 18:15:50 GMT
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

## 13. Database Access Restricted to VM Only

### 13.1 PostgreSQL listens on loopback only

```bash
ss -tlnp | grep 5432
```

**Expected output:**
```
LISTEN 0      244        127.0.0.1:5432      0.0.0.0:*
LISTEN 0      244            [::1]:5432         [::]:*
```

### 13.2 PostgreSQL `listen_addresses` is `localhost`

```bash
sudo grep listen_addresses /etc/postgresql/15/main/postgresql.conf
```

**Expected output:**
```
#listen_addresses = 'localhost'         # what IP address(es) to listen on;
```

> **Note:** The default value `localhost` is in effect — PostgreSQL does not bind to any external interface.

### 13.3 Connection to PostgreSQL from host machine fails

```powershell
xh GET http://localhost:5432/
```

**Expected output:**
```
xh: error: error sending request for url (http://localhost:5432/)
Caused by:
    0: client error (Connect)
    1: tcp connect error
    2: No connection could be made because the target machine actively refused it. (os error 10061)
```

> **Note:** Port 5432 is not forwarded in the Vagrantfile, and PostgreSQL only binds to `127.0.0.1` inside the VM. The database is completely inaccessible from outside.

---

## 14. Database Migration Script

The app binary includes a `-migrate` flag used in `ExecStartPre` of the systemd service unit. The migration creates the `notes` table using `CREATE TABLE IF NOT EXISTS`, making it idempotent.

### 14.1 `notes` table exists after provisioning

```bash
sudo -u postgres psql -d mywebapp -c '\dt'
```

**Expected output:**
```
         List of relations
 Schema | Name  | Type  |  Owner
--------+-------+-------+----------
 public | notes | table | mywebapp
(1 row)
```

### 14.2 Table schema matches the spec

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

### 14.3 Migration is idempotent — runs again without errors

```bash
sudo -u app /usr/local/bin/mywebapp -migrate
```

**Expected output:**
```
2026/05/24 18:25:22 migration done
```

> **Note:** Running migration on an already-migrated database succeeds without errors, because `CREATE TABLE IF NOT EXISTS` is used.

---

## 15. Nginx Access Log

Verify that nginx is writing request logs to `/var/log/nginx/mywebapp_access.log`.

```bash
sudo tail -15 /var/log/nginx/mywebapp_access.log
```

**Expected output:**
```
10.0.2.2 - - [24/May/2026:16:38:00 +0000] "GET /health/alive HTTP/1.1" 404 125 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:17:44:05 +0000] "GET /health/alive HTTP/1.1" 404 125 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:17:44:39 +0000] "GET /health/ready HTTP/1.1" 404 125 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:17:45:23 +0000] "GET / HTTP/1.1" 200 173 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:17:46:21 +0000] "POST /notes HTTP/1.1" 201 118 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:18:07:37 +0000] "POST /notes HTTP/1.1" 201 104 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:18:07:56 +0000] "GET /notes HTTP/1.1" 200 118 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:18:09:02 +0000] "GET /notes HTTP/1.1" 200 158 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:18:11:45 +0000] "GET /notes/1 HTTP/1.1" 200 118 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:18:11:55 +0000] "GET /notes/3 HTTP/1.1" 200 118 "-" "xh/0.25.3"
127.0.0.1 - - [24/May/2026:18:12:34 +0000] "GET /notes/3 HTTP/1.1" 200 179 "-" "xh/0.25.3"
10.0.2.2 - - [24/May/2026:18:13:35 +0000] "GET / HTTP/1.1" 200 173 "-" "xh/0.25.3"
10.0.2.2 - - [24/May/2026:18:13:58 +0000] "GET / HTTP/1.1" 200 173 "-" "xh/0.25.3"
10.0.2.2 - - [24/May/2026:18:14:49 +0000] "GET /notes HTTP/1.1" 200 118 "-" "xh/0.25.3"
10.0.2.2 - - [24/May/2026:18:15:50 +0000] "GET /health/alive HTTP/1.1" 404 125 "-" "xh/0.25.3"
```

> **Note:** `10.0.2.2` is the host machine IP as seen from the VM (Vagrant NAT). `127.0.0.1` is from inside the VM.

