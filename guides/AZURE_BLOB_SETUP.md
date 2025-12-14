# Azure Blob Storage Setup Guide

## Quick Start (5 minutes)

### Step 1: Create Azure Storage Account

**Option A: Azure Portal (GUI)**
1. Go to [Azure Portal](https://portal.azure.com)
2. Create Resource → Storage Account
3. Settings:
   - Name: `satishdocsstorage` (must be unique)
   - Region: Same as your container (e.g., East US)
   - Performance: Standard
   - Redundancy: LRS (Locally Redundant)
4. Click **Create**

**Option B: Azure CLI**
```bash
# Login to Azure
az login

# Create storage account
az storage account create \
  --name satishdocsstorage \
  --resource-group my-rg \
  --location eastus \
  --sku Standard_LRS

# Create container
az storage container create \
  --name satish-documents \
  --account-name satishdocsstorage
```

### Step 2: Get Connection String

**Portal:**
1. Go to Storage Account → Access Keys
2. Copy **Connection string** from key1 or key2

**CLI:**
```bash
az storage account show-connection-string \
  --name satishdocsstorage \
  --resource-group my-rg \
  --output tsv
```

### Step 3: Configure Locally

Add to your `.env` file:
```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=satishdocsstorage;AccountKey=xxxxx;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER=satish-documents
```

### Step 4: Upload Documents

```bash
# Upload all documents from data/documents/
python scripts/upload_to_blob.py

# Or manually via Azure Portal:
# Storage Account → Containers → satish-documents → Upload
```

### Step 5: Test Locally

```bash
# Test download and indexing
.\startup-with-blob.bat

# Or Docker
docker build -t satish-ai-assistant .
docker run -p 8501:8501 `
  -e OPENAI_API_KEY=your_key `
  -e AZURE_STORAGE_CONNECTION_STRING="your_connection_string" `
  -e AZURE_STORAGE_CONTAINER=satish-documents `
  satish-ai-assistant
```

---

## Document Management Workflow

### Adding New Documents

**1. Upload to Blob Storage**
```bash
# Add document locally
cp new-project.pdf data/documents/

# Upload to blob
python scripts/upload_to_blob.py
```

**2. Restart Container**
```bash
az container restart --name satish-ai-assistant --resource-group my-rg
```

**Done!** Container downloads latest documents and re-indexes.

### Updating Existing Documents

```bash
# Update local file
edit data/documents/FAQs.md

# Upload (overwrites existing)
python scripts/upload_to_blob.py

# Restart container
az container restart --name satish-ai-assistant --resource-group my-rg
```

### Viewing Documents

```bash
# List all documents in blob storage
python scripts/upload_to_blob.py --list

# Or use Azure Storage Explorer (GUI)
# https://azure.microsoft.com/en-us/products/storage/storage-explorer/
```

---

## Azure Deployment with Blob Storage

### Deploy to Azure Container Instances

```bash
# 1. Build and push image
docker build -t satish-ai-assistant .
az acr login --name myregistry
docker tag satish-ai-assistant myregistry.azurecr.io/satish-ai-assistant:latest
docker push myregistry.azurecr.io/satish-ai-assistant:latest

# 2. Deploy with Blob Storage environment variables
az container create \
  --resource-group my-rg \
  --name satish-ai-assistant \
  --image myregistry.azurecr.io/satish-ai-assistant:latest \
  --dns-name-label satish-ai \
  --ports 8501 \
  --cpu 1 --memory 1.5 \
  --registry-login-server myregistry.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --environment-variables \
    OPENAI_API_KEY=<your_key> \
    AZURE_STORAGE_CONNECTION_STRING="<connection_string>" \
    AZURE_STORAGE_CONTAINER=satish-documents \
  --restart-policy Always
```

### Deploy to Azure App Service

```bash
# 1. Create App Service Plan
az appservice plan create \
  --name satish-ai-plan \
  --resource-group my-rg \
  --is-linux \
  --sku B1

# 2. Create Web App
az webapp create \
  --resource-group my-rg \
  --plan satish-ai-plan \
  --name satish-ai-assistant \
  --deployment-container-image-name myregistry.azurecr.io/satish-ai-assistant:latest

# 3. Configure environment variables
az webapp config appsettings set \
  --name satish-ai-assistant \
  --resource-group my-rg \
  --settings \
    OPENAI_API_KEY=<your_key> \
    AZURE_STORAGE_CONNECTION_STRING="<connection_string>" \
    AZURE_STORAGE_CONTAINER=satish-documents \
    WEBSITES_PORT=8501
```

---

## Startup Process with Blob Storage

When your container starts:

```
1. Container starts
   ↓
2. startup-with-blob.sh executes
   ↓
3. Checks AZURE_STORAGE_CONNECTION_STRING
   ↓
4. Downloads ALL documents from blob storage
   → satish-documents/* → /app/data/documents/
   ↓
5. Falls back to bundled docs if blob unavailable
   ↓
6. Runs init_vectordb.py
   → Indexes all documents
   → Creates ChromaDB with ~25-50 chunks
   ↓
7. Starts Streamlit on port 8501
   ↓
8. Ready to answer questions! 🚀
```

**Total startup time:** 40-60 seconds (including document download)

---

## Troubleshooting

### Documents not downloading

**Check logs:**
```bash
az container logs --name satish-ai-assistant --resource-group my-rg
```

**Look for:**
```
✅ Downloaded 5 documents from blob storage
✅ Vector database initialized successfully
```

**If you see:**
```
⚠️  Blob storage not configured, using bundled documents
```

→ Check environment variables are set correctly.

### Connection string issues

**Test connection:**
```bash
python -c "
from azure.storage.blob import BlobServiceClient
import os
client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'))
print('✅ Connection successful')
"
```

### Slow startup

- Documents download on every restart (adds 10-20 seconds)
- Consider keeping small documents (<5MB total) in blob
- Large files (videos, datasets) should use Azure Files or CDN

---

## Cost Optimization

### Same Region = Free Egress
```bash
# ✅ GOOD: Same region
Storage: East US
Container: East US
→ No bandwidth charges

# ❌ BAD: Different regions
Storage: West US
Container: East US
→ $0.02/GB egress
```

### Lifecycle Management

Auto-delete old document versions:
```bash
az storage account management-policy create \
  --account-name satishdocsstorage \
  --policy @policy.json
```

**policy.json:**
```json
{
  "rules": [
    {
      "name": "deleteOldVersions",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"]
        },
        "actions": {
          "version": {
            "delete": {
              "daysAfterCreationGreaterThan": 30
            }
          }
        }
      }
    }
  ]
}
```

---

## Security Best Practices

### 1. Use Managed Identity (Production)

Instead of connection strings, use managed identity:

```bash
# Enable managed identity for container
az container create \
  --assign-identity [system] \
  # ... other parameters

# Grant storage access
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee <managed-identity-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/satishdocsstorage
```

Update `startup-with-blob.sh` to use DefaultAzureCredential.

### 2. Restrict Network Access

```bash
# Allow only your container's IP
az storage account network-rule add \
  --account-name satishdocsstorage \
  --ip-address <container-ip>
```

### 3. Enable Soft Delete

Recover accidentally deleted documents:
```bash
az storage blob service-properties delete-policy update \
  --account-name satishdocsstorage \
  --enable true \
  --days-retained 7
```

---

## Monitoring

### View Storage Metrics

**Portal:** Storage Account → Metrics

**CLI:**
```bash
az monitor metrics list \
  --resource /subscriptions/<sub-id>/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/satishdocsstorage \
  --metric Transactions
```

### Set Alerts

```bash
az monitor metrics alert create \
  --name high-blob-requests \
  --resource-group my-rg \
  --scopes /subscriptions/<sub-id>/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/satishdocsstorage \
  --condition "total Transactions > 10000" \
  --description "Alert when blob requests exceed 10k"
```

---

## Next Steps

1. ✅ Create storage account
2. ✅ Upload documents
3. ✅ Test locally with blob download
4. ✅ Deploy to Azure with environment variables
5. ✅ Verify documents download on startup
6. ✅ Test queries work correctly

**Ready to deploy!** See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for full deployment guide.
