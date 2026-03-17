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

# Set PYTHONPATH so absolute imports starting with "app." work correctly
ENV PYTHONPATH=/app

# Expose the default API port (Cloud Run will set PORT)
EXPOSE 8080

# Command to start the FastAPI server.
# Use the PORT environment variable provided by Cloud Run, defaulting to 8080.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
