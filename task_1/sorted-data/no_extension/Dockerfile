# Use official Python image (multi-arch: works on Apple Silicon)
FROM python:3.10-slim

# Optional: system deps for building psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Set workdir inside the container
WORKDIR /app

# Reduce Python noise and disable .pyc creation
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Upgrade pip first
RUN pip install --upgrade pip

# Copy dependency file first to leverage Docker layer cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose the app port (FastAPI default when using uvicorn below)
EXPOSE 8000

# Start FastAPI via uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
