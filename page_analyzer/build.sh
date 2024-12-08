#!/usr/bin/env bash

set -euo pipefail

echo "Installing dependencies..."
make install

echo "Initializing database structure..."
psql -a -d "$DATABASE_URL" -f database.sql