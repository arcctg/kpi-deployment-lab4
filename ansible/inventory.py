#!/usr/bin/env python3
"""Dynamic Ansible inventory backed by Terraform outputs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


TERRAFORM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "terraform")


def run_terraform_output() -> dict:
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=TERRAFORM_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("terraform executable not found in PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Failed to read terraform outputs. Run `terraform apply` in the terraform/ directory first.\n"
            f"{exc.stderr.strip()}"
        ) from exc

    return json.loads(result.stdout or "{}")


def build_inventory(outputs: dict) -> dict:
    worker_name = outputs["worker_name"]["value"]
    db_name = outputs["db_vm_name"]["value"]
    worker_ip = outputs["worker_ip"]["value"]
    db_ip = outputs["db_ip"]["value"]

    host_vars = {
        worker_name: {
            "ansible_host": worker_ip,
            "ansible_user": "ansible",
        },
        db_name: {
            "ansible_host": db_ip,
            "ansible_user": "ansible",
        },
    }

    return {
        "_meta": {"hostvars": host_vars},
        "workers": {"hosts": [worker_name]},
        "db": {"hosts": [db_name]},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--host", dest="host")
    args = parser.parse_args()

    outputs = run_terraform_output()
    inventory = build_inventory(outputs)

    if args.list or (not args.host and len(sys.argv) == 1):
        print(json.dumps(inventory, indent=2))
        return

    if args.host:
        hostvars = inventory["_meta"]["hostvars"].get(args.host, {})
        print(json.dumps(hostvars, indent=2))
        return

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
