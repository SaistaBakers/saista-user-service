#!/bin/sh
set -e

echo "[entrypoint] Running database migration..."
python migrate_db.py

echo "[entrypoint] Starting user-service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5001
