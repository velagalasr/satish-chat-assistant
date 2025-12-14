#!/bin/bash
# Startup script for Azure deployment
# This script initializes the vector database before starting the Streamlit app

echo "====================================="
echo "Starting Satish's AI Assistant"
echo "====================================="

# Initialize vector database from documents
echo "Initializing RAG vector database..."
python scripts/init_vectordb.py

if [ $? -eq 0 ]; then
    echo "✅ Vector database initialized successfully"
else
    echo "⚠️  Warning: Vector database initialization had issues"
fi

echo ""
echo "Starting Streamlit application..."
echo "====================================="

# Start Streamlit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
