#! /usr/bin/env bash

set -e
set -x

# Let the DB start
uv run python app/backend_pre_start.py

# Create initial data in DB
uv run python app/initial_data.py

# Seed credit card data for the default dev user (skips if data already exists)
SEED_EMAIL="dev@francocalvo.ar"
HAS_CARDS=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc \
    "SELECT COUNT(*) FROM credit_card WHERE user_id = (SELECT id FROM \"user\" WHERE email = '${SEED_EMAIL}')")
if [ "${HAS_CARDS}" = "0" ]; then
    echo "Seeding credit card data for ${SEED_EMAIL}..."
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        -f scripts/seed_credit_cards.sql
else
    echo "Credit card data already exists for ${SEED_EMAIL}, skipping seed."
fi
