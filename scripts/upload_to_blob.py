"""
Upload documents to Azure Blob Storage
Usage: python scripts/upload_to_blob.py
"""

import os
import sys
from pathlib import Path
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def upload_documents():
    """Upload all documents from data/documents to Azure Blob Storage"""
    
    # Get configuration from environment
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "satish-documents")
    documents_path = Path("data/documents")
    
    if not connection_string:
        print("❌ Error: AZURE_STORAGE_CONNECTION_STRING not found in environment")
        print("Please add it to your .env file:")
        print("AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...")
        return False
    
    if not documents_path.exists():
        print(f"❌ Error: Documents directory not found: {documents_path}")
        return False
    
    try:
        # Initialize Blob Service Client
        print(f"🔗 Connecting to Azure Blob Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get or create container
        try:
            container_client = blob_service_client.get_container_client(container_name)
            if not container_client.exists():
                print(f"📦 Creating container: {container_name}")
                container_client.create_container()
            else:
                print(f"📦 Using existing container: {container_name}")
        except Exception as e:
            print(f"❌ Error accessing container: {e}")
            return False
        
        # Find all documents
        document_files = []
        for ext in ['*.pdf', '*.txt', '*.md', '*.docx', '*.doc']:
            document_files.extend(documents_path.glob(ext))
        
        if not document_files:
            print(f"⚠️  No documents found in {documents_path}")
            return False
        
        print(f"\n📄 Found {len(document_files)} documents to upload:\n")
        
        # Upload each document
        uploaded_count = 0
        skipped_count = 0
        
        for file_path in document_files:
            blob_name = file_path.name
            
            try:
                # Check if blob already exists
                blob_client = container_client.get_blob_client(blob_name)
                
                # Get content type based on extension
                content_type = get_content_type(file_path.suffix)
                
                # Upload with content type
                with open(file_path, "rb") as data:
                    print(f"  ⬆️  Uploading: {blob_name} ({file_path.stat().st_size / 1024:.1f} KB)")
                    blob_client.upload_blob(
                        data, 
                        overwrite=True,
                        content_settings=ContentSettings(content_type=content_type)
                    )
                
                uploaded_count += 1
                print(f"     ✅ Uploaded successfully")
                
            except Exception as e:
                print(f"     ❌ Failed to upload {blob_name}: {e}")
                skipped_count += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Upload Complete!")
        print(f"{'='*60}")
        print(f"  Uploaded: {uploaded_count} documents")
        if skipped_count > 0:
            print(f"  Failed: {skipped_count} documents")
        print(f"  Container: {container_name}")
        print(f"  Location: {blob_service_client.account_name}.blob.core.windows.net/{container_name}")
        print(f"{'='*60}\n")
        
        # List all blobs in container
        print("📋 Documents in container:")
        blobs = container_client.list_blobs()
        for blob in blobs:
            print(f"  • {blob.name} ({blob.size / 1024:.1f} KB)")
        
        return uploaded_count > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_content_type(extension: str) -> str:
    """Get content type for file extension"""
    content_types = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
    }
    return content_types.get(extension.lower(), 'application/octet-stream')


def list_documents():
    """List all documents in Blob Storage"""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "satish-documents")
    
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING not found")
        return
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        print(f"\n📋 Documents in {container_name}:\n")
        blobs = container_client.list_blobs()
        for blob in blobs:
            print(f"  • {blob.name} ({blob.size / 1024:.1f} KB) - Last modified: {blob.last_modified}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage documents in Azure Blob Storage")
    parser.add_argument("--list", action="store_true", help="List documents in blob storage")
    args = parser.parse_args()
    
    if args.list:
        list_documents()
    else:
        upload_documents()
