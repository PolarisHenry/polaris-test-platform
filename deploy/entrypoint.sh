#!/bin/sh
set -e

rm -rf ./migrations

# Wait for MySQL to be ready
echo "Waiting for MySQL..."
sleep 30
echo "Assuming MySQL is ready"

aerich init -t app.settings.TORTOISE_ORM
aerich init-db
aerich migrate
aerich upgrade
nginx
python run.py