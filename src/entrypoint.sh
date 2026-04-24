#!/bin/sh
set -e

# The migration-job.yaml handles the primary DB initialisation before this
# pod is ever scheduled. This call is a no-op safety net (all tables already
# exist) and guards against edge cases like manual pod restarts before the Job
# has run in a fresh cluster.
echo "[entrypoint] Running migration safety check..."
python migrate_db.py

echo "[entrypoint] Starting user-service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5001
