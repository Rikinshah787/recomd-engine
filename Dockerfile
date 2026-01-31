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

# Copy startup script
COPY start.sh .
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV NUM_PRODUCTS=500

# Expose the port
EXPOSE 8000

# Start the application using the startup script
CMD ["./start.sh"]
