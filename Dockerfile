# Use official slim Python image
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

RUN useradd --create-home appuser
WORKDIR /app

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

COPY requirements.txt ./requirements.txt

RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy full source code
COPY . /app


COPY models/ /app/models/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "inference.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
