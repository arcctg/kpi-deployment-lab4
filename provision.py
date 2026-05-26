#!/usr/bin/env python3

import subprocess
import sys
import os
import shutil

VAGRANT_HOME = "/home/vagrant"
STUDENT_HOME = "/home/student"
TEACHER_HOME = "/home/teacher"
OPERATOR_HOME = "/home/operator"
APP_SRC = "/vagrant/app"
DEPLOY_SRC = "/vagrant/deploy"
BINARY_DEST = "/usr/local/bin/mywebapp"
CONFIG_DIR = "/etc/mywebapp"
CONFIG_DEST = f"{CONFIG_DIR}/config.yaml"
SYSTEMD_DIR = "/etc/systemd/system"
NGINX_SITES_AVAILABLE = "/etc/nginx/sites-available"
NGINX_SITES_ENABLED = "/etc/nginx/sites-enabled"
SUDOERS_DIR = "/etc/sudoers.d"


def run(cmd, **kwargs):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"FAILED: {cmd}", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def user_exists(name):
    r = subprocess.run(f"id {name}", shell=True, capture_output=True)
    return r.returncode == 0


def step_install_packages():
    run("apt-get update -qq")
    run("apt-get install -y -qq postgresql nginx golang sudo wget")
    
    run("wget -q https://github.com/ducaale/xh/releases/download/v0.25.3/xh-v0.25.3-x86_64-unknown-linux-musl.tar.gz -O /tmp/xh.tar.gz && tar -xzf /tmp/xh.tar.gz -C /usr/local/bin --strip-components=1 xh-v0.25.3-x86_64-unknown-linux-musl/xh && rm /tmp/xh.tar.gz")


def step_create_users():
    if not user_exists("student"):
        run("useradd -m -s /bin/bash student")
    run("usermod -aG sudo student")
    run("echo 'student:12345678' | chpasswd")

    if not user_exists("teacher"):
        run("useradd -m -s /bin/bash teacher")
    run("usermod -aG sudo teacher")
    run("echo 'teacher:12345678' | chpasswd")
    run("chage -d 0 teacher")

    if not user_exists("app"):
        run("useradd -r -s /usr/sbin/nologin app")

    if not user_exists("operator"):
        run("useradd -m -s /bin/bash -g operator operator")
    run("echo 'operator:12345678' | chpasswd")
    run("chage -d 0 operator")


def step_configure_ssh_auth():
    ssh_config_path = "/etc/ssh/sshd_config.d/01-password-auth.conf"
    os.makedirs(os.path.dirname(ssh_config_path), exist_ok=True)
    with open(ssh_config_path, "w") as f:
        f.write("PasswordAuthentication yes\n")
    run("systemctl restart ssh")


def step_setup_postgres():
    run("systemctl start postgresql")
    run("systemctl enable postgresql")

    user_check = run("sudo -u postgres psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='mywebapp'\"")
    if user_check != "1":
        run("sudo -u postgres psql -c \"CREATE ROLE mywebapp WITH LOGIN PASSWORD 'mywebapp'\"")

    db_check = run("sudo -u postgres psql -tAc \"SELECT 1 FROM pg_database WHERE datname='mywebapp'\"")
    if db_check != "1":
        run("sudo -u postgres createdb -O mywebapp mywebapp")


def step_build_app():
    env = os.environ.copy()
    env["GOPATH"] = "/tmp/gopath"
    env["HOME"] = "/root"

    tidy = subprocess.run(
        "go mod tidy",
        shell=True, capture_output=True, text=True, cwd=APP_SRC, env=env
    )
    if tidy.returncode != 0:
        print(tidy.stdout, file=sys.stderr)
        print(tidy.stderr, file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        f"go build -o {BINARY_DEST} .",
        shell=True, capture_output=True, text=True, cwd=APP_SRC, env=env
    )
    if result.returncode != 0:
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    run(f"chmod 755 {BINARY_DEST}")


def step_deploy_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    shutil.copy(f"{DEPLOY_SRC}/config.yaml", CONFIG_DEST)
    run(f"chown root:app {CONFIG_DEST}")
    run(f"chmod 640 {CONFIG_DEST}")


def step_deploy_systemd():
    shutil.copy(f"{DEPLOY_SRC}/mywebapp.service", f"{SYSTEMD_DIR}/mywebapp.service")
    shutil.copy(f"{DEPLOY_SRC}/mywebapp.socket", f"{SYSTEMD_DIR}/mywebapp.socket")
    run("systemctl daemon-reload")
    run("systemctl enable mywebapp.socket")
    run("systemctl start mywebapp.socket")
    run("systemctl enable mywebapp.service")
    run("systemctl start mywebapp.service")


def step_configure_nginx():
    run("rm -f /etc/nginx/sites-enabled/default")
    shutil.copy(f"{DEPLOY_SRC}/nginx.conf", f"{NGINX_SITES_AVAILABLE}/mywebapp")
    link = f"{NGINX_SITES_ENABLED}/mywebapp"
    if not os.path.exists(link):
        os.symlink(f"{NGINX_SITES_AVAILABLE}/mywebapp", link)
    run("nginx -t")
    run("systemctl enable nginx")
    run("systemctl restart nginx")


def step_deploy_sudoers():
    dest = f"{SUDOERS_DIR}/operator"
    shutil.copy(f"{DEPLOY_SRC}/sudoers-operator", dest)
    run(f"chmod 440 {dest}")
    run(f"chown root:root {dest}")


def step_create_gradebook():
    run(f"mkdir -p {STUDENT_HOME}")
    with open(f"{STUDENT_HOME}/gradebook", "w") as f:
        f.write("9\n")
    run(f"chown student:student {STUDENT_HOME}/gradebook")


def step_migrate_ssh_keys():
    ssh_dir = f"{STUDENT_HOME}/.ssh"
    os.makedirs(ssh_dir, exist_ok=True)
    src_keys = f"{VAGRANT_HOME}/.ssh/authorized_keys"
    dst_keys = f"{ssh_dir}/authorized_keys"
    if os.path.exists(src_keys):
        shutil.copy(src_keys, dst_keys)
    run(f"chown -R student:student {ssh_dir}")
    run(f"chmod 700 {ssh_dir}")
    run(f"chmod 600 {dst_keys}")


def step_lock_vagrant():
    run("usermod -L vagrant")
    run("chsh -s /usr/sbin/nologin vagrant")


def main():
    steps = [
        ("Installing packages",           step_install_packages),
        ("Creating users",                step_create_users),
        ("Configuring SSH password auth", step_configure_ssh_auth),
        ("Setting up PostgreSQL",         step_setup_postgres),
        ("Building Go application",       step_build_app),
        ("Deploying application config",  step_deploy_config),
        ("Deploying systemd units",       step_deploy_systemd),
        ("Configuring nginx",             step_configure_nginx),
        ("Deploying sudoers rules",       step_deploy_sudoers),
        ("Creating gradebook",            step_create_gradebook),
        ("Migrating SSH keys to student", step_migrate_ssh_keys),
        ("Locking vagrant user",          step_lock_vagrant),
    ]

    for name, fn in steps:
        print(f"==> {name}")
        fn()
        print(f"    OK")

    print("\n==> Provisioning complete")


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Must run as root", file=sys.stderr)
        sys.exit(1)
    main()
