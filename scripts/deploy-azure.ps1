# Azure Container App Deployment Script (Windows PowerShell)
# Run this once to set up your Azure infrastructure

# Configuration - UPDATE THESE VALUES
$RESOURCE_GROUP = "chatbot-rg"
$LOCATION = "eastus"
$ACR_NAME = "satishacr"  # Must be globally unique, lowercase, no special chars
$STORAGE_ACCOUNT = "satishdocsstorage"
$STORAGE_CONTAINER = "satish-documents"
$CONTAINER_APP_ENV = "satish-ai-env"
$CONTAINER_APP_NAME = "satish-ai-assistant"
$IMAGE_NAME = "satish-ai-assistant"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Azure Container App Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Login to Azure
Write-Host "1. Logging in to Azure..." -ForegroundColor Yellow
az login
az account show

$confirm = Read-Host "Is this the correct subscription? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Available subscriptions:"
    az account list --output table
    $subId = Read-Host "Enter subscription ID"
    az account set --subscription $subId
}

# 2. Create Resource Group
Write-Host ""
Write-Host "2. Creating resource group..." -ForegroundColor Yellow
az group create --name $RESOURCE_GROUP --location $LOCATION

# 3. Create Azure Container Registry
Write-Host ""
Write-Host "3. Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $ACR_NAME `
  --sku Basic `
  --admin-enabled true

# Get ACR credentials
Write-Host ""
Write-Host "ACR Credentials (save for GitHub secrets):" -ForegroundColor Green
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv
Write-Host "ACR_USERNAME: $ACR_USERNAME"
Write-Host "ACR_PASSWORD: $ACR_PASSWORD"

# 4. Create Storage Account
Write-Host ""
Write-Host "4. Creating storage account..." -ForegroundColor Yellow
az storage account create `
  --name $STORAGE_ACCOUNT `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --sku Standard_LRS

# Create container
az storage container create `
  --name $STORAGE_CONTAINER `
  --account-name $STORAGE_ACCOUNT

# Get connection string
Write-Host ""
Write-Host "Storage Connection String (save for GitHub secrets):" -ForegroundColor Green
$STORAGE_CONNECTION = az storage account show-connection-string --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --output tsv
Write-Host $STORAGE_CONNECTION

# 5. Create Container App Environment
Write-Host ""
Write-Host "5. Creating Container App Environment..." -ForegroundColor Yellow
az containerapp env create `
  --name $CONTAINER_APP_ENV `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION

# 6. Build and push initial image
Write-Host ""
Write-Host "6. Building and pushing Docker image..." -ForegroundColor Yellow
az acr build `
  --registry $ACR_NAME `
  --image "${IMAGE_NAME}:latest" `
  --file Dockerfile `
  .

# 7. Create Container App
Write-Host ""
Write-Host "7. Creating Container App..." -ForegroundColor Yellow

$OPENAI_KEY = Read-Host "Enter your OpenAI API Key" -AsSecureString
$OPENAI_KEY_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($OPENAI_KEY))

az containerapp create `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_APP_ENV `
  --image "${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest" `
  --target-port 8501 `
  --ingress external `
  --registry-server "${ACR_NAME}.azurecr.io" `
  --registry-username $ACR_USERNAME `
  --registry-password $ACR_PASSWORD `
  --cpu 1 `
  --memory 2Gi `
  --min-replicas 1 `
  --max-replicas 1 `
  --secrets `
    openai-api-key=$OPENAI_KEY_PLAIN `
    azure-storage-connection="$STORAGE_CONNECTION" `
  --env-vars `
    OPENAI_API_KEY=secretref:openai-api-key `
    AZURE_STORAGE_CONNECTION_STRING=secretref:azure-storage-connection `
    AZURE_STORAGE_CONTAINER=$STORAGE_CONTAINER

# 8. Get app URL
Write-Host ""
Write-Host "8. Getting application URL..." -ForegroundColor Yellow
$APP_URL = az containerapp show `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query properties.configuration.ingress.fqdn `
  --output tsv

# 9. Create service principal for GitHub Actions
Write-Host ""
Write-Host "9. Creating service principal for GitHub Actions..." -ForegroundColor Yellow
$SUBSCRIPTION_ID = az account show --query id -o tsv
$AZURE_CREDENTIALS = az ad sp create-for-rbac `
  --name "${CONTAINER_APP_NAME}-github" `
  --role contributor `
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" `
  --sdk-auth

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your app is live at: https://$APP_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "GitHub Secrets to Add:" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. OPENAI_API_KEY"
Write-Host $OPENAI_KEY_PLAIN
Write-Host ""
Write-Host "2. AZURE_STORAGE_CONNECTION_STRING"
Write-Host $STORAGE_CONNECTION
Write-Host ""
Write-Host "3. ACR_USERNAME"
Write-Host $ACR_USERNAME
Write-Host ""
Write-Host "4. ACR_PASSWORD"
Write-Host $ACR_PASSWORD
Write-Host ""
Write-Host "5. AZURE_CREDENTIALS"
Write-Host $AZURE_CREDENTIALS
Write-Host ""
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:"
Write-Host "1. Add all 5 secrets to GitHub: https://github.com/velagalasr/satish-chat-assistant/settings/secrets/actions"
Write-Host "2. Update .github/workflows/azure-deploy.yml with:"
Write-Host "   - REGISTRY_NAME: $ACR_NAME"
Write-Host "   - RESOURCE_GROUP: $RESOURCE_GROUP"
Write-Host "   - CONTAINER_APP_NAME: $CONTAINER_APP_NAME"
Write-Host "3. Upload documents: python scripts/upload_to_blob.py"
Write-Host "4. Push to GitHub to trigger auto-deploy"
Write-Host ""
Write-Host "Future updates: Just 'git push' and it auto-deploys!" -ForegroundColor Green
