#!/bin/bash
# Azure Container App Deployment Script
# Run this once to set up your Azure infrastructure

# Configuration - UPDATE THESE VALUES
RESOURCE_GROUP="chatbot-rg"
LOCATION="eastus"
ACR_NAME="satishacr"  # Must be globally unique, lowercase, no special chars
STORAGE_ACCOUNT="satishdocsstorage"
STORAGE_CONTAINER="satish-documents"
CONTAINER_APP_ENV="satish-ai-env"
CONTAINER_APP_NAME="satish-ai-assistant"
IMAGE_NAME="satish-ai-assistant"

echo "=========================================="
echo "Azure Container App Deployment"
echo "=========================================="
echo ""

# 1. Login to Azure
echo "1. Logging in to Azure..."
az login
az account show

read -p "Is this the correct subscription? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please set the correct subscription:"
    az account list --output table
    read -p "Enter subscription ID: " SUB_ID
    az account set --subscription "$SUB_ID"
fi

# 2. Create Resource Group
echo ""
echo "2. Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# 3. Create Azure Container Registry
echo ""
echo "3. Creating Azure Container Registry..."
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Get ACR credentials
echo ""
echo "📋 ACR Credentials (save for GitHub secrets):"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
echo "ACR_USERNAME: $ACR_USERNAME"
echo "ACR_PASSWORD: $ACR_PASSWORD"

# 4. Create Storage Account (if doesn't exist)
echo ""
echo "4. Creating storage account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create container
az storage container create \
  --name $STORAGE_CONTAINER \
  --account-name $STORAGE_ACCOUNT

# Get connection string
echo ""
echo "📋 Storage Connection String (save for GitHub secrets):"
STORAGE_CONNECTION=$(az storage account show-connection-string --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --output tsv)
echo "$STORAGE_CONNECTION"

# 5. Create Container App Environment
echo ""
echo "5. Creating Container App Environment..."
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# 6. Build and push initial image
echo ""
echo "6. Building and pushing Docker image..."
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_NAME:latest \
  --file Dockerfile \
  .

# 7. Create Container App
echo ""
echo "7. Creating Container App..."

# Prompt for OpenAI API key
read -p "Enter your OpenAI API Key: " OPENAI_KEY

az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME:latest \
  --target-port 8501 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu 1 \
  --memory 2Gi \
  --min-replicas 1 \
  --max-replicas 1 \
  --secrets \
    openai-api-key=$OPENAI_KEY \
    azure-storage-connection="$STORAGE_CONNECTION" \
  --env-vars \
    OPENAI_API_KEY=secretref:openai-api-key \
    AZURE_STORAGE_CONNECTION_STRING=secretref:azure-storage-connection \
    AZURE_STORAGE_CONTAINER=$STORAGE_CONTAINER

# 8. Get app URL
echo ""
echo "8. Getting application URL..."
APP_URL=$(az containerapp show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

# 9. Create service principal for GitHub Actions
echo ""
echo "9. Creating service principal for GitHub Actions..."
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
AZURE_CREDENTIALS=$(az ad sp create-for-rbac \
  --name "$CONTAINER_APP_NAME-github" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth)

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🌐 Your app is live at: https://$APP_URL"
echo ""
echo "📋 GitHub Secrets to Add:"
echo "=========================================="
echo ""
echo "1. OPENAI_API_KEY"
echo "$OPENAI_KEY"
echo ""
echo "2. AZURE_STORAGE_CONNECTION_STRING"
echo "$STORAGE_CONNECTION"
echo ""
echo "3. ACR_USERNAME"
echo "$ACR_USERNAME"
echo ""
echo "4. ACR_PASSWORD"
echo "$ACR_PASSWORD"
echo ""
echo "5. AZURE_CREDENTIALS"
echo "$AZURE_CREDENTIALS"
echo ""
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Add all 5 secrets to GitHub: https://github.com/velagalasr/satish-chat-assistant/settings/secrets/actions"
echo "2. Update .github/workflows/azure-deploy.yml with:"
echo "   - REGISTRY_NAME: $ACR_NAME"
echo "   - RESOURCE_GROUP: $RESOURCE_GROUP"
echo "   - CONTAINER_APP_NAME: $CONTAINER_APP_NAME"
echo "3. Upload documents: python scripts/upload_to_blob.py"
echo "4. Push to GitHub to trigger auto-deploy"
echo ""
echo "🚀 Future updates: Just 'git push' and it auto-deploys!"
