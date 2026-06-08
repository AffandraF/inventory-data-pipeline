FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for build, psycopg2 and mysqlconnector
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY config/ ./config/
COPY src/ ./src/
COPY tests/ ./tests/
COPY docker/entrypoint.sh ./docker/

# Make entrypoint executable
RUN chmod +x ./docker/entrypoint.sh

ENTRYPOINT ["/bin/bash", "./docker/entrypoint.sh"]
