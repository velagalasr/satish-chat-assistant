# Document Management in Azure

## Overview
Your documents (resume, FAQs, project details) need to be available for vector indexing on every container restart. You have two options:

---

## Option 1: Bundle Documents in Docker Image (Recommended)

### How It Works
Documents are **built into the Docker image** during build time.

```
Local: data/documents/
  ├── SatishVelagala Resume.pdf
  ├── FAQs.md
  ├── Project-1-Details.pdf
  └── About-Me.txt
        ↓ (docker build)
Docker Image: /app/data/documents/
  ├── Resume.pdf
  ├── FAQs.md
  ├── Project-1-Details.pdf
  └── About-Me.txt
        ↓ (container starts)
startup.sh → init_vectordb.py
        ↓
ChromaDB (indexed from bundled docs)
```

### Adding/Updating Documents

**Step 1:** Add documents locally
```bash
cp new-document.pdf data/documents/
git add data/documents/new-document.pdf
git commit -m "Add new project details"
```

**Step 2:** Rebuild Docker image
```bash
docker build -t satish-ai-assistant:v2 .
docker tag satish-ai-assistant:v2 myregistry.azurecr.io/satish-ai-assistant:v2
docker push myregistry.azurecr.io/satish-ai-assistant:v2
```

**Step 3:** Update Azure deployment
```bash
# Azure Container Instances
az container create --name satish-ai-assistant --image myregistry.azurecr.io/satish-ai-assistant:v2 ...

# Or Azure App Service
az webapp config container set --name satish-ai-assistant --docker-custom-image-name myregistry.azurecr.io/satish-ai-assistant:v2
```

**On Container Start:**
1. Documents are in `/app/data/documents/` (from image)
2. `init_vectordb.py` indexes all documents
3. ChromaDB ready with all your content
4. App serves requests

### Pros & Cons

**Pros:**
- ✅ Simple, reliable, version-controlled
- ✅ No extra Azure storage costs ($0)
- ✅ Documents always available (bundled)
- ✅ Works offline (no dependency on external storage)

**Cons:**
- ❌ Need rebuild/redeploy to update documents (~5 min)
- ❌ Not ideal for frequently changing content (daily updates)

**Best For:** 
- Portfolio sites (your use case)
- Documents that change weekly/monthly
- Static knowledge bases

---

## Option 2: Azure Blob Storage (For Dynamic Content)

### How It Works
Documents stored in Azure Blob Storage, downloaded on container start.

```
Azure Blob Storage:
  satish-documents/
    ├── Resume.pdf
    ├── FAQs.md
    └── Projects.pdf
        ↓ (container starts)
startup-with-blob.sh downloads all blobs
        ↓
/app/data/documents/ (temporary)
        ↓
init_vectordb.py indexes
        ↓
ChromaDB ready
```

### Setup

**1. Create Blob Storage**
```bash
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

**2. Upload documents**
```bash
az storage blob upload \
  --account-name satishdocsstorage \
  --container-name satish-documents \
  --name Resume.pdf \
  --file data/documents/Resume.pdf

# Or use Azure Storage Explorer (GUI)
```

**3. Update Dockerfile**
```dockerfile
# Use startup-with-blob.sh instead
COPY startup-with-blob.sh startup.sh
RUN chmod +x startup.sh
```

**4. Configure environment variables**
```bash
az webapp config appsettings set \
  --name satish-ai-assistant \
  --settings \
    AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..." \
    AZURE_STORAGE_CONTAINER="satish-documents"
```

### Adding/Updating Documents

**Upload to Blob Storage:**
```bash
# Option 1: Azure CLI
az storage blob upload \
  --account-name satishdocsstorage \
  --container-name satish-documents \
  --name new-project.pdf \
  --file new-project.pdf \
  --overwrite

# Option 2: Azure Storage Explorer (GUI)
# Option 3: Azure Portal (upload in browser)
```

**Restart container:**
```bash
az container restart --name satish-ai-assistant --resource-group my-rg
```

**On Container Start:**
1. Downloads ALL documents from Blob Storage
2. Saves to `/app/data/documents/`
3. `init_vectordb.py` indexes them
4. App ready with latest content

### Pros & Cons

**Pros:**
- ✅ Update documents without rebuilding Docker image
- ✅ Upload via Azure Portal/Explorer (no code deploy)
- ✅ Instant updates (just restart container)
- ✅ Can update from anywhere

**Cons:**
- ❌ Extra cost (~$0.50-1/month for storage + requests)
- ❌ Slightly slower startup (~10-20 sec download time)
- ❌ Dependency on external service
- ❌ More complex setup

**Best For:**
- Frequently changing documents (daily/weekly)
- Multiple people managing content
- Need to update without code deployment

---

## Comparison

| Aspect | Docker Image | Azure Blob |
|--------|--------------|------------|
| **Update Process** | Rebuild + redeploy | Upload + restart |
| **Time to Update** | ~5 minutes | ~30 seconds |
| **Cost** | $0 | ~$1/month |
| **Complexity** | Simple | Moderate |
| **Version Control** | Git (code) | Blob versioning |
| **Startup Time** | 20-30 sec | 30-50 sec |
| **Offline Works** | Yes | No |

---

## Recommended: Docker Image Bundling

For your portfolio with resume + FAQs + project details:

### Current Structure
```
data/documents/
├── SatishVelagala Resume.pdf       # Your main resume
├── FAQs.md                         # Common questions
├── Project-GenAI-Platform.pdf      # Project 1 details
├── Project-Fraud-Detection.pdf     # Project 2 details
└── Skills-Certifications.md        # Additional info
```

### Workflow
```bash
# 1. Add/update documents locally
echo "Updated content" > data/documents/FAQs.md

# 2. Commit to Git
git add data/documents/
git commit -m "Update FAQs"
git push

# 3. Rebuild and deploy
docker build -t satish-ai-assistant:latest .
docker push myregistry.azurecr.io/satish-ai-assistant:latest

# 4. Azure auto-deploys (if CI/CD configured)
# Or manually restart:
az container restart --name satish-ai-assistant --resource-group my-rg
```

### On Every Container Start
```
Container starts
    ↓
Documents in image: /app/data/documents/
    ├── Resume.pdf
    ├── FAQs.md
    ├── Project-1.pdf
    ├── Project-2.pdf
    └── Skills.md
    ↓
startup.sh → init_vectordb.py
    ↓
Indexes 5 documents → ~25-50 chunks
    ↓
ChromaDB ready (in-memory)
    ↓
Streamlit starts
    ↓
Users can ask about any content
```

**Total startup time:** ~30-40 seconds

---

## Testing Locally

### Test with bundled documents:
```bash
# Add documents
cp myfiles/*.pdf data/documents/

# Run startup script
./startup.bat  # Windows
./startup.sh   # Linux/Mac

# Or with Docker
docker build -t test .
docker run -p 8501:8501 -e OPENAI_API_KEY=key test
```

### Verify documents loaded:
```bash
# Check logs
docker logs <container-id>

# Should see:
# Initializing RAG vector database...
# Successfully indexed 25 document chunks
# ✅ Vector database initialized successfully
```

---

## File Size Considerations

| Document Type | Typical Size | Chunks (800 chars) |
|--------------|--------------|-------------------|
| Resume PDF | 100-200 KB | 3-5 chunks |
| FAQ Markdown | 10-50 KB | 2-10 chunks |
| Project PDF | 200-500 KB | 5-15 chunks |
| Total (5 docs) | ~1 MB | 15-50 chunks |

**Indexing time:** 20-40 seconds (depends on document count and OpenAI API)

---

## Deployment Checklist

- [ ] All documents in `data/documents/`
- [ ] Documents committed to Git
- [ ] Tested locally with `startup.sh`
- [ ] Docker image builds successfully
- [ ] Pushed to Azure Container Registry
- [ ] Environment variables set (OPENAI_API_KEY)
- [ ] Container deployed to Azure
- [ ] Health check passes
- [ ] Test queries work
- [ ] Check logs for "Vector database initialized"

---

## Next Steps

1. **Add your documents** to `data/documents/`
2. **Test locally** with `startup.bat`
3. **Commit to Git**
4. **Deploy to Azure** following AZURE_DEPLOYMENT.md

Your documents will be bundled, indexed on startup, and ready for questions! 🚀
