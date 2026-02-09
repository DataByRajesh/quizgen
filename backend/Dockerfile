FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for pdfplumber/python-docx
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY backend /app/backend

EXPOSE 8000

ENV PORT=8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
