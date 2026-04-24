# Builder stage
FROM python:3.9-slim AS builder

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.9-slim

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy all application source (app/, migrate_db.py, entrypoint.sh, requirements.txt)
COPY src/ .

RUN chown -R appuser:appuser /app \
    && chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 5001
ENTRYPOINT ["/app/entrypoint.sh"]
