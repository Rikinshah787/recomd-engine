# Use Python 3.10 slim as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for FAISS and building packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Generate data and embeddings during build
RUN python scripts/generate_data.py && python scripts/build_embeddings.py

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Start the application
# We use 0.0.0.0 to allow external connections on Railway
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
