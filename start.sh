#!/bin/bash
set -e

# Generate data if it doesn't exist
if [ ! -f "data/products_clean.json" ]; then
    echo "📦 Data not found, generating..."
    python scripts/generate_data.py
    python scripts/build_embeddings.py
else
    echo "✅ Data found, skipping generation."
fi

# Start the application
echo "🚀 Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
