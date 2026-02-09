#! /usr/bin/env bash

set -e
set -x

# Let the DB start
uv run python app/backend_pre_start.py

# Create initial data in DB
uv run python app/initial_data.py

# Seed credit card data for default users (skips if data already exists)
for email in "dev@francocalvo.ar" "alo@gmail.com"; do
    # Only seed if user has no credit cards yet
    HAS_CARDS=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc \
        "SELECT COUNT(*) FROM credit_card WHERE user_id = (SELECT id FROM \"user\" WHERE email = '${email}')")
    if [ "${HAS_CARDS}" = "0" ]; then
        echo "Seeding credit card data for ${email}..."
        PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_SERVER}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
            -v user_email="'${email}'" \
            -f scripts/seed_credit_cards.sql
    else
        echo "Credit card data already exists for ${email}, skipping seed."
    fi
done
