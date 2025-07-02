FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including SQLite3, curl for healthcheck, and poppler for PDF processing
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/uploads

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
# test
