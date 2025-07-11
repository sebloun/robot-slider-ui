# Use official Python 3.12 Alpine image
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Install required system dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    && pip install --no-cache-dir --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Copy application code
COPY robot robot/
COPY static static/
COPY templates templates/
COPY app.py .

# Run the application (production)
CMD ["python", "app.py"]
