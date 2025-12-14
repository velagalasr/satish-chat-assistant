"""
Download documents from Azure Blob Storage
Used by startup-with-blob.sh during container initialization
"""

import os
import sys
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def download_documents():
    """Download all documents from Azure Blob Storage to data/documents/"""
    
    # Get configuration from environment
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "satish-documents")
    documents_path = Path("data/documents")
    
    if not connection_string:
        print("⚠️  AZURE_STORAGE_CONNECTION_STRING not found")
        print("Using bundled documents in container")
        return False
    
    try:
        # Ensure documents directory exists
        documents_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Blob Service Client
        print(f"🔗 Connecting to Azure Blob Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        # Check if container exists
        if not container_client.exists():
            print(f"⚠️  Container '{container_name}' not found")
            print("Using bundled documents")
            return False
        
        # List and download all blobs
        blobs = list(container_client.list_blobs())
        
        if not blobs:
            print(f"⚠️  No documents found in container '{container_name}'")
            print("Using bundled documents")
            return False
        
        print(f"📥 Downloading {len(blobs)} documents from blob storage...\n")
        
        downloaded_count = 0
        for blob in blobs:
            try:
                blob_client = container_client.get_blob_client(blob.name)
                download_path = documents_path / blob.name
                
                print(f"  ⬇️  {blob.name} ({blob.size / 1024:.1f} KB)")
                
                with open(download_path, "wb") as download_file:
                    download_file.write(blob_client.download_blob().readall())
                
                downloaded_count += 1
                print(f"     ✅ Downloaded to {download_path}")
                
            except Exception as e:
                print(f"     ❌ Failed to download {blob.name}: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ Downloaded {downloaded_count} documents from blob storage")
        print(f"{'='*60}\n")
        
        return downloaded_count > 0
        
    except Exception as e:
        print(f"❌ Error connecting to blob storage: {e}")
        print("Using bundled documents")
        return False


if __name__ == "__main__":
    success = download_documents()
    sys.exit(0 if success else 1)
