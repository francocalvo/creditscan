#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Garage (layout + bucket/key provisioning).
#
# Why: Garage will return "Layout not ready" until a layout is assigned/applied.
# If Garage metadata is wiped (e.g. docker volumes removed), keys/buckets also
# disappear, and the backend will fail with AccessDenied.
#
# Usage:
#   docker compose up -d garage
#   ./scripts/garage-bootstrap.sh
#
# If credentials are missing or invalid, the script can create a Garage key and
# persist it back to .env for local development.
#   GARAGE_BOOTSTRAP_WRITE_ENV=1 ./scripts/garage-bootstrap.sh

COMPOSE_CMD=${COMPOSE_CMD:-"docker compose"}
GARAGE_SERVICE=${GARAGE_SERVICE:-garage}
ENV_FILE_PATH=${GARAGE_BOOTSTRAP_ENV_FILE:-.env}
WRITE_ENV=${GARAGE_BOOTSTRAP_WRITE_ENV:-1}

# Layout defaults
GARAGE_ZONE=${GARAGE_ZONE:-dc1}
GARAGE_CAPACITY=${GARAGE_CAPACITY:-1G}

# Optionally load .env (shell-style). Disable with GARAGE_BOOTSTRAP_SOURCE_ENV=0
if [ "${GARAGE_BOOTSTRAP_SOURCE_ENV:-1}" = "1" ] && [ -f "$ENV_FILE_PATH" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ENV_FILE_PATH"
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

strip_ansi() {
  sed -E 's/\x1B\[[0-9;]*[[:alpha:]]//g'
}

is_valid_garage_key_id() {
  printf "%s" "$1" | grep -Eq '^GK[0-9a-f]+$'
}

upsert_env_var() {
  local key="$1"
  local value="$2"
  local file="$ENV_FILE_PATH"

  if [ "$WRITE_ENV" != "1" ]; then
    return 0
  fi

  if [ ! -f "$file" ]; then
    touch "$file"
  fi

  if grep -qE "^${key}=" "$file"; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" "$file"
    rm -f "${file}.bak"
  else
    printf "\n%s=%s\n" "$key" "$value" >>"$file"
  fi
}

create_key() {
  local key_name="$1"
  local create_out
  local new_key
  local new_secret

  create_out=$(gexec key create "$key_name" 2>&1 || true)
  new_key=$(printf "%s\n" "$create_out" | strip_ansi | awk '/Key ID:/{print $3; exit}')
  new_secret=$(printf "%s\n" "$create_out" | strip_ansi | awk '/Secret key:/{print $3; exit}')

  if [ -z "$new_key" ] || [ -z "$new_secret" ]; then
    return 1
  fi

  printf "%s;%s\n" "$new_key" "$new_secret"
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

# Resolve access key:
# 1) use existing key from env if valid
# 2) try import when key id format is valid
# 3) create a new key and persist into .env
resolved_key=""
resolved_secret=""

if [ -n "$S3_ACCESS_KEY" ] && [ -n "$S3_SECRET_KEY" ]; then
  if gexec key info "$S3_ACCESS_KEY" >/dev/null 2>&1; then
    echo "Access key exists: $S3_ACCESS_KEY"
    resolved_key="$S3_ACCESS_KEY"
    resolved_secret="$S3_SECRET_KEY"
  elif is_valid_garage_key_id "$S3_ACCESS_KEY"; then
    echo "Importing access key: $S3_ACCESS_KEY (name: $S3_KEY_NAME)"
    if gexec key import --yes -n "$S3_KEY_NAME" "$S3_ACCESS_KEY" "$S3_SECRET_KEY" >/dev/null 2>&1; then
      resolved_key="$S3_ACCESS_KEY"
      resolved_secret="$S3_SECRET_KEY"
    else
      echo "Warning: key import failed; falling back to generated key" >&2
    fi
  else
    echo "Warning: S3_ACCESS_KEY '$S3_ACCESS_KEY' is not a valid Garage key ID; generating a Garage key" >&2
  fi
elif [ -n "$S3_ACCESS_KEY" ] || [ -n "$S3_SECRET_KEY" ]; then
  echo "Warning: incomplete S3 credentials in env; generating a Garage key" >&2
fi

if [ -z "$resolved_key" ] || [ -z "$resolved_secret" ]; then
  generated_key=$(create_key "$S3_KEY_NAME" || true)
  if [ -z "$generated_key" ]; then
    echo "Warning: could not create key with name '$S3_KEY_NAME', retrying with unique name" >&2
    generated_key=$(create_key "${S3_KEY_NAME}-$(date +%s)")
  fi

  resolved_key=${generated_key%%;*}
  resolved_secret=${generated_key#*;}
  echo "Created key: $resolved_key"
fi

echo "Granting bucket permissions (R/W/Owner)"
gexec bucket allow --read --write --owner "$S3_BUCKET" --key "$resolved_key" >/dev/null

upsert_env_var "S3_ACCESS_KEY" "$resolved_key"
upsert_env_var "S3_SECRET_KEY" "$resolved_secret"
upsert_env_var "S3_BUCKET" "$S3_BUCKET"
if [ "$WRITE_ENV" = "1" ]; then
  echo "Persisted S3 credentials to $ENV_FILE_PATH"
fi

echo "Garage bootstrap complete"
