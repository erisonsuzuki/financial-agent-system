#!/bin/sh
set -e

cd /code/app
python scripts/migrate.py

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
