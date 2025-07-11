# Use official Python 3.12 Alpine image
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Install required system dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    && pip install --no-cache-dir --upgrade pip

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Copy application code
COPY robot .

# Run the application (production)
CMD ["python", "app.py"]