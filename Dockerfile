FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set PYTHONPATH so absolute imports starting with "app." work securely
ENV PYTHONPATH=/app

# Expose the default API port
EXPOSE 8080

# Command to start the FastAPI server (using shell form to read environment variables)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
