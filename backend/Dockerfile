FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    libssl-dev \
    gcc \
    weasyprint \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Render injects PORT env var; fall back to 8000 locally
CMD gunicorn main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:${PORT:-8000} --timeout 120
