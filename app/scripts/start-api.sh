#!/bin/sh
set -e

cd /code
python -m app.scripts.migrate

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
