#!/bin/bash
# Enhanced startup script with Azure Blob Storage support
# Downloads documents from Blob Storage before indexing

echo "====================================="
echo "Starting Satish's AI Assistant"
echo "====================================="

# Check if Azure Blob Storage is configured
if [ ! -z "$AZURE_STORAGE_CONNECTION_STRING" ]; then
    echo "Downloading documents from Azure Blob Storage..."
    
    # Install Azure CLI if not present
    pip install azure-storage-blob --quiet
    
    # Download all documents from blob container
    python - <<EOF
from azure.storage.blob import BlobServiceClient
import os

connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
container_name = os.getenv('AZURE_STORAGE_CONTAINER', 'satish-documents')

blob_service = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service.get_container_client(container_name)

# Create documents directory
os.makedirs('data/documents', exist_ok=True)

# Download all blobs
for blob in container_client.list_blobs():
    blob_client = container_client.get_blob_client(blob)
    download_path = f"data/documents/{blob.name}"
    
    with open(download_path, "wb") as file:
        file.write(blob_client.download_blob().readall())
    
    print(f"Downloaded: {blob.name}")

print(f"✅ All documents downloaded from Blob Storage")
EOF

    if [ $? -ne 0 ]; then
        echo "⚠️  Warning: Failed to download from Blob Storage, using bundled documents"
    fi
else
    echo "Using documents bundled in Docker image"
fi

# Initialize vector database from documents
echo ""
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
