# Use official slim Python image
FROM python:3.10-slim

# Avoid buffering (helps logs)
ENV PYTHONUNBUFFERED=1

# Create app user and workdir
RUN useradd --create-home appuser
WORKDIR /app

# Install OS deps needed for pyarrow (parquet) and mlflow (if used)
# Keep minimal. Add packages as required by your environment.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    libpq-dev \
    libffi-dev \
    g++ \
    python3-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt ./requirements.txt

# Upgrade pip and install requirements
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy app code (only necessary files)
# We copy everything except what is excluded by .dockerignore
COPY . /app

# Ensure models file exists in image (if you keep template model committed)
# If the model is not committed, you'll need to mount it at runtime or build after creating it.
# Create non-root user and chown
RUN chown -R appuser:appuser /app
USER appuser

# Expose API port
EXPOSE 8000

# Production-ready command (single worker)
CMD ["uvicorn", "inference.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
