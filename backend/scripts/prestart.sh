#! /usr/bin/env bash

set -e
set -x

# Let the DB start
uv run python app/backend_pre_start.py

# Create initial data in DB
uv run python app/initial_data.py
