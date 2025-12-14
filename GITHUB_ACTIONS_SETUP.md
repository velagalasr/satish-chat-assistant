# GitHub Actions Auto-Deploy Setup

Your project is configured for automatic deployment to Azure on every push to `main`/`master` branch.

## 🔧 Setup GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

### 1. **OPENAI_API_KEY**
```
sk-proj-...
```
Your OpenAI API key

### 2. **AZURE_STORAGE_CONNECTION_STRING**
```
DefaultEndpointsProtocol=https;AccountName=satishdocsstorage;AccountKey=...;EndpointSuffix=core.windows.net
```
From Azure Portal → Storage Account → Access Keys

### 3. **ACR_USERNAME**
```
satishchatbotregistry-dxbbhvcag6dph3gw
```
Your Azure Container Registry name

### 4. **ACR_PASSWORD**
```
<password from ACR>
```
From Azure Portal → Container Registry → Access Keys → password

### 5. **AZURE_CREDENTIALS**
```json
{
  "clientId": "xxx",
  "clientSecret": "xxx",
  "subscriptionId": "xxx",
  "tenantId": "xxx"
}
```

**Get this by running:**
```bash
az ad sp create-for-rbac \
  --name "satish-ai-assistant-deploy" \
  --role contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/<resource-group> \
  --sdk-auth
```

---

## 🚀 How It Works

```
1. Push to GitHub (main branch)
   ↓
2. GitHub Actions triggers
   ↓
3. Builds Docker image
   ↓
4. Pushes to Azure Container Registry
   ↓
5. Updates secrets (OpenAI API key, Blob connection)
   ↓
6. Deploys to Azure Container Apps
   ↓
7. Container starts:
   - Downloads documents from blob
   - Initializes vector database
   - Starts Streamlit
   ↓
8. ✅ Live in ~3-5 minutes!
```

---

## 📝 Update Environment Variables

Edit `.github/workflows/azure-deploy.yml`:

```yaml
env:
  REGISTRY_NAME: satishchatbotregistry-dxbbhvcag6dph3gw  # Your ACR
  IMAGE_NAME: satish-ai-assistant
  RESOURCE_GROUP: chatbot-rg  # Your resource group
  CONTAINER_APP_NAME: satish-ai-assistant  # Your container app name
```

---

## ✅ Test Auto-Deploy

```bash
# Make a small change
echo "# Test deploy" >> README.md

# Commit and push
git add .
git commit -m "Test auto-deploy"
git push

# Watch deployment
# Go to GitHub → Actions tab
# See logs in real-time
```

---

## 🔍 Monitor Deployment

**GitHub Actions:**
- https://github.com/velagalasr/satish-chat-assistant/actions

**View logs:**
```bash
az containerapp logs show \
  --name satish-ai-assistant \
  --resource-group chatbot-rg \
  --follow
```

---

## 🛠️ Manual Deployment Trigger

You can also trigger deployment manually:
- Go to GitHub → Actions
- Select "Deploy to Azure Container Apps"
- Click "Run workflow"

---

## 📊 Deployment Time

- **Build:** ~2-3 minutes
- **Push to ACR:** ~30 seconds
- **Deploy:** ~1-2 minutes
- **Container Start:** ~40-60 seconds (downloads documents + indexes)

**Total:** ~4-6 minutes from push to live

---

## 🔄 Update Workflow

If you need to change resources or settings, edit:
```
.github/workflows/azure-deploy.yml
```

Then commit and push - changes take effect immediately.

---

## 🚨 Troubleshooting

### Deployment fails?
```bash
# Check Actions logs on GitHub
# Or check Azure logs:
az containerapp logs show --name satish-ai-assistant --resource-group chatbot-rg
```

### Secrets not working?
- Verify all 5 secrets are set in GitHub
- Check secret names match exactly (case-sensitive)
- Re-create AZURE_CREDENTIALS if stale

### Container not starting?
- Check blob storage connection string is correct
- Verify documents exist in `satish-documents` container
- Check OpenAI API key is valid

---

## 🎯 Next Steps

1. ✅ Add all 5 GitHub secrets
2. ✅ Update env variables in workflow
3. ✅ Push to trigger first deployment
4. ✅ Monitor in GitHub Actions
5. ✅ Access your live app!

**Your deployment URL:**
```
https://satish-ai-assistant.<region>.azurecontainerapps.io
```
