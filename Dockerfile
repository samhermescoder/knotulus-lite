# Use a slim Python image; Cloud Run sets PORT.
FROM python:3.12-slim

WORKDIR /app

# System deps for any native wheels
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run injects PORT; gunicorn runs the gateway (Agent Gateway primitive)
ENV PORT=8080
EXPOSE 8080

CMD exec gunicorn src.gateway:app --bind :$PORT --workers 1 --timeout 300
