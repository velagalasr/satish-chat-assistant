# Azure Deployment Guide for Satish's AI Assistant

## Deployment Overview
This application auto-initializes the RAG vector database on every startup, ensuring vectors are always available even after container restarts.

## Prerequisites
- Azure subscription
- Azure CLI installed
- Docker installed (for local testing)
- OpenAI API key

## Option 1: Azure Container Instances (Simplest)

### 1. Build and push Docker image

```bash
# Login to Azure Container Registry
az acr login --name <your-registry-name>

# Build image
docker build -t satish-ai-assistant:latest .

# Tag for ACR
docker tag satish-ai-assistant:latest <your-registry>.azurecr.io/satish-ai-assistant:latest

# Push to ACR
docker push <your-registry>.azurecr.io/satish-ai-assistant:latest
```

### 2. Deploy to Azure Container Instances

```bash
az container create \
  --resource-group <your-rg> \
  --name satish-ai-assistant \
  --image <your-registry>.azurecr.io/satish-ai-assistant:latest \
  --dns-name-label satish-ai-assistant \
  --ports 8501 \
  --environment-variables \
    OPENAI_API_KEY=<your-key> \
  --cpu 2 \
  --memory 4
```

## Option 2: Azure App Service (Container)

### 1. Create App Service Plan

```bash
az appservice plan create \
  --name satish-ai-plan \
  --resource-group <your-rg> \
  --is-linux \
  --sku B2
```

### 2. Create Web App

```bash
az webapp create \
  --resource-group <your-rg> \
  --plan satish-ai-plan \
  --name satish-ai-assistant \
  --deployment-container-image-name <your-registry>.azurecr.io/satish-ai-assistant:latest
```

### 3. Configure Environment Variables

```bash
az webapp config appsettings set \
  --resource-group <your-rg> \
  --name satish-ai-assistant \
  --settings \
    OPENAI_API_KEY=<your-key> \
    WEBSITES_PORT=8501
```

## Option 3: Azure Kubernetes Service (Production Scale)

See `deployment/kubernetes/` for Kubernetes manifests.

## Environment Variables Required

```env
OPENAI_API_KEY=sk-...              # Required
AZURE_OPENAI_API_KEY=...           # Optional (if using Azure OpenAI)
AZURE_OPENAI_ENDPOINT=...          # Optional
TAVILY_API_KEY=...                 # Optional (web search)
```

## Startup Process

On each container start:
1. **Vector DB initialization** (~20-30 seconds)
   - Loads documents from `data/documents/`
   - Creates embeddings (OpenAI API)
   - Stores in ChromaDB
   
2. **Streamlit app starts**
   - Connects to initialized ChromaDB
   - Ready to serve requests

## Cost Considerations

### Container Resources
- **CPU:** 2 cores (for embedding generation)
- **Memory:** 4GB (ChromaDB + Streamlit + models)
- **Estimated:** ~$50-80/month (Azure Container Instances)

### OpenAI API Costs
- **Embeddings:** ~$0.0001 per 1K tokens
- **Resume indexing:** ~$0.01 per restart
- **Chat (GPT-3.5):** ~$0.002 per conversation
- **Estimated:** ~$5-10/month (light usage)

**Total: ~$60-90/month**

## Testing Locally

```bash
# Test startup script
./startup.sh

# Or with Docker
docker build -t satish-ai-assistant:latest .
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=<your-key> \
  satish-ai-assistant:latest
```

Visit: http://localhost:8501

## Monitoring Startup

Check container logs to verify initialization:

```bash
# Azure Container Instances
az container logs --resource-group <rg> --name satish-ai-assistant

# Azure App Service
az webapp log tail --resource-group <rg> --name satish-ai-assistant
```

Look for:
```
Initializing RAG vector database...
✅ Vector database initialized successfully
Starting Streamlit application...
```

## Troubleshooting

### Issue: Slow startup (>60 seconds)
**Solution:** Increase health check `start-period` in Dockerfile

### Issue: Out of memory
**Solution:** Increase container memory to 4GB or 8GB

### Issue: OpenAI API timeout
**Solution:** Check OPENAI_API_KEY environment variable

### Issue: Resume not found
**Solution:** Ensure `data/documents/SatishVelagala Resume.pdf` is in Docker image

## Custom Domain Setup

1. **Add custom domain to App Service:**
```bash
az webapp config hostname add \
  --webapp-name satish-ai-assistant \
  --resource-group <rg> \
  --hostname chat.satishvelagala.com
```

2. **Enable HTTPS:**
```bash
az webapp config ssl create \
  --resource-group <rg> \
  --name satish-ai-assistant \
  --hostname chat.satishvelagala.com
```

## Updating the Application

### Update resume/documents:
1. Replace `data/documents/SatishVelagala Resume.pdf`
2. Rebuild and push Docker image
3. Restart container (auto re-indexes)

### Update code:
1. Make changes
2. Rebuild Docker image
3. Push to registry
4. Restart container

## Security Best Practices

1. **API Keys:** Use Azure Key Vault
2. **Network:** Restrict to HTTPS only
3. **CORS:** Configure in `config/config.yaml`
4. **Rate Limiting:** Add Azure Front Door

## Support

For issues, check:
- Container logs
- ChromaDB initialization output
- OpenAI API status
- Network connectivity

---

**Deployment Status:** ✅ Ready for Azure deployment with auto-initialization
