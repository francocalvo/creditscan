#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Garage (layout + optional bucket/key provisioning).
#
# Why: Garage will return "Layout not ready" until a layout is assigned/applied.
# If Garage metadata is wiped (e.g. docker volumes removed), keys/buckets also
# disappear, and the backend will fail with AccessDenied.
#
# Usage:
#   docker compose up -d garage
#   ./scripts/garage-bootstrap.sh
#
# Optional (recommended): provide S3 creds and bucket via env/.env so the script
# can import the key and grant bucket access:
#   S3_ACCESS_KEY=... S3_SECRET_KEY=... S3_BUCKET=... ./scripts/garage-bootstrap.sh

COMPOSE_CMD=${COMPOSE_CMD:-"docker compose"}
GARAGE_SERVICE=${GARAGE_SERVICE:-garage}

# Layout defaults
GARAGE_ZONE=${GARAGE_ZONE:-dc1}
GARAGE_CAPACITY=${GARAGE_CAPACITY:-1G}

# Optionally load .env (shell-style). Disable with GARAGE_BOOTSTRAP_SOURCE_ENV=0
if [ "${GARAGE_BOOTSTRAP_SOURCE_ENV:-1}" = "1" ] && [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

S3_BUCKET=${S3_BUCKET:-app-storage}
S3_ACCESS_KEY=${S3_ACCESS_KEY:-}
S3_SECRET_KEY=${S3_SECRET_KEY:-}
S3_KEY_NAME=${S3_KEY_NAME:-backend-key}

wait_for_container() {
  local cid
  local i
  for i in $(seq 1 60); do
    cid=$($COMPOSE_CMD ps -q "$GARAGE_SERVICE" 2>/dev/null || true)
    if [ -n "$cid" ]; then
      echo "$cid"
      return 0
    fi
    sleep 1
  done
  echo "Error: garage container not found (service '$GARAGE_SERVICE')" >&2
  return 1
}

cid=$(wait_for_container)

gexec() {
  docker exec "$cid" /garage "$@"
}

echo "Bootstrapping Garage (container: $cid)"

# Ensure layout is assigned/applied.
status_out=$(gexec status 2>/dev/null || true)
node_id=$(printf "%s\n" "$status_out" | awk 'BEGIN{h=0} /^==== HEALTHY NODES ====$/{h=1; next} h && $1 ~ /^[0-9a-f]{16}$/ {print $1; exit}')

if [ -z "$node_id" ]; then
  echo "Error: could not determine Garage node ID from 'garage status'" >&2
  echo "$status_out" >&2
  exit 1
fi

if printf "%s\n" "$status_out" | grep -q "NO ROLE ASSIGNED"; then
  cur_ver=$(gexec layout show 2>/dev/null | awk -F': ' '/Current cluster layout version:/{print $2}' || true)
  if [ -z "$cur_ver" ]; then
    cur_ver=0
  fi
  new_ver=$((cur_ver + 1))

  echo "Applying layout (node=$node_id zone=$GARAGE_ZONE cap=$GARAGE_CAPACITY version=$new_ver)"
  gexec layout assign -z "$GARAGE_ZONE" -c "$GARAGE_CAPACITY" "$node_id" >/dev/null
  gexec layout apply --version "$new_ver" >/dev/null
else
  echo "Layout already assigned"
fi

# Ensure the bucket exists.
if ! gexec bucket info "$S3_BUCKET" >/dev/null 2>&1; then
  echo "Creating bucket: $S3_BUCKET"
  gexec bucket create "$S3_BUCKET" >/dev/null
else
  echo "Bucket exists: $S3_BUCKET"
fi

# Ensure the access key exists (import if provided).
if [ -n "$S3_ACCESS_KEY" ] && [ -n "$S3_SECRET_KEY" ]; then
  if ! gexec key info "$S3_ACCESS_KEY" >/dev/null 2>&1; then
    echo "Importing access key: $S3_ACCESS_KEY (name: $S3_KEY_NAME)"
    gexec key import --yes -n "$S3_KEY_NAME" "$S3_ACCESS_KEY" "$S3_SECRET_KEY" >/dev/null
  else
    echo "Access key exists: $S3_ACCESS_KEY"
  fi

  echo "Granting bucket permissions (R/W/Owner)"
  gexec bucket allow --read --write --owner "$S3_BUCKET" --key "$S3_ACCESS_KEY" >/dev/null
else
  echo "Skipping key import/permissions (set S3_ACCESS_KEY + S3_SECRET_KEY to enable)"
fi

echo "Garage bootstrap complete"
