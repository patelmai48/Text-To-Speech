# Multi-stage production Dockerfile for VoxAI Studio
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies needed for compiling psycopg2 and audio packages if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final lightweight production image
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . .

# Create non-root application user for container security
RUN useradd -m voxaiuser && \
    mkdir -p static/audio && \
    chown -R voxaiuser:voxaiuser /app

USER voxaiuser

EXPOSE 5000

ENV FLASK_ENV=production
ENV PORT=5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "wsgi:app"]
