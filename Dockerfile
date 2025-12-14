# Use Python 3.12 slim image (compatible with ChromaDB)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/chromadb data/faiss data/documents data/evaluation/results

# Make startup scripts executable
RUN chmod +x startup.sh startup-with-blob.sh

# Expose Streamlit port
EXPOSE 8501

# Health check (allow more time for startup initialization)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set environment variables for better performance
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true

# Run startup script with Blob Storage support (includes document download + vector DB initialization)
CMD ["./startup-with-blob.sh"]
