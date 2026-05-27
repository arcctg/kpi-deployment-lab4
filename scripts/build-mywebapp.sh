#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}/app"

mkdir -p "${ROOT}/ansible/roles/app/files"
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -o "${ROOT}/ansible/roles/app/files/mywebapp" .
