#!/usr/bin/env bash
set -euo pipefail

docker compose up -d garage
bash scripts/garage-bootstrap.sh
exec docker compose watch "$@"
