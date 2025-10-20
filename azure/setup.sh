#!/bin/bash
# Azure Setup Script for FYP Stock Analyzer
# This script sets up all required Azure resources for deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}FYP Stock Analyzer - Azure Setup${NC}"
echo "================================================"

# Configuration variables
RESOURCE_GROUP="fyp-stock-analyzer-rg"
LOCATION="eastus"
ACR_NAME="fypstockanalyzer"
SUBSCRIPTION_ID=""

# Function to print colored messages
print_step() {
    echo -e "${BLUE}Step: $1${NC}"
}

print_success() {
    echo -e "${GREEN}Success: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

print_error() {
    echo -e "${RED}Error: $1${NC}"
}

# Check if Azure CLI is installed
print_step "Checking Azure CLI installation..."
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first:"
    echo "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi
print_success "Azure CLI is installed"

# Login to Azure
print_step "Logging into Azure..."
if ! az account show &> /dev/null; then
    print_warning "Not logged into Azure. Starting login process..."
    az login
else
    print_success "Already logged into Azure"
fi

# Get subscription ID
if [ -z "$SUBSCRIPTION_ID" ]; then
    SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    print_success "Using subscription: $SUBSCRIPTION_ID"
fi

# Create resource group
print_step "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

print_success "Resource group created"

# Deploy Azure Container Registry
print_step "Deploying Azure Container Registry..."
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file azure/container-registry.json \
    --parameters registryName=$ACR_NAME \
    --output table

print_success "Azure Container Registry deployed"

# Get ACR credentials
print_step "Getting ACR credentials..."
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

print_success "ACR Login Server: $ACR_LOGIN_SERVER"

# Create service principal for GitHub Actions
print_step "Creating service principal for GitHub Actions..."
SP_NAME="fyp-github-actions-sp"
SP_JSON=$(az ad sp create-for-rbac \
    --name $SP_NAME \
    --role contributor \
    --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
    --sdk-auth)

print_success "Service principal created"

# Display GitHub Secrets
echo ""
echo -e "${YELLOW}GitHub Secrets Configuration${NC}"
echo "================================================"
echo "Add these secrets to your GitHub repository:"
echo "Settings → Secrets and variables → Actions → New repository secret"
echo ""
echo -e "${GREEN}AZURE_CREDENTIALS:${NC}"
echo "$SP_JSON"
echo ""
echo -e "${GREEN}AZURE_RESOURCE_GROUP:${NC} $RESOURCE_GROUP"
echo -e "${GREEN}AZURE_REGISTRY_USERNAME:${NC} $ACR_USERNAME"
echo -e "${GREEN}AZURE_REGISTRY_PASSWORD:${NC} $ACR_PASSWORD"
echo ""
echo -e "${GREEN}STAGING_DATABASE_URL:${NC} mongodb://admin:[MONGO_STAGING_PASSWORD]@localhost:27017/fyp_staging"
echo -e "${GREEN}PRODUCTION_DATABASE_URL:${NC} mongodb://admin:[MONGO_PRODUCTION_PASSWORD]@localhost:27017/fyp_production"
echo ""

# Save configuration to file
CONFIG_FILE="azure-config.txt"
print_step "Saving configuration to $CONFIG_FILE..."
cat > $CONFIG_FILE << EOF
# Azure Configuration for FYP Stock Analyzer
# Generated on $(date)

Resource Group: $RESOURCE_GROUP
Location: $LOCATION
ACR Name: $ACR_NAME
ACR Login Server: $ACR_LOGIN_SERVER
Subscription ID: $SUBSCRIPTION_ID

# GitHub Secrets (copy these to GitHub):
AZURE_CREDENTIALS=$SP_JSON
AZURE_RESOURCE_GROUP=$RESOURCE_GROUP
AZURE_REGISTRY_USERNAME=$ACR_USERNAME
AZURE_REGISTRY_PASSWORD=$ACR_PASSWORD
STAGING_DATABASE_URL=mongodb://admin:[SET_YOUR_MONGO_STAGING_PASSWORD]@localhost:27017/fyp_staging
PRODUCTION_DATABASE_URL=mongodb://admin:[SET_YOUR_MONGO_PRODUCTION_PASSWORD]@localhost:27017/fyp_production
EOF

print_success "Configuration saved to $CONFIG_FILE"

echo ""
echo -e "${BLUE}Azure setup complete!${NC}"
echo "================================================"
echo "Next steps:"
echo "1. Add the GitHub secrets shown above to your repository"
echo "2. Push code to main branch to trigger CI/CD pipeline"
echo "3. Monitor deployment in GitHub Actions"
echo ""
echo -e "${YELLOW}Quick commands:${NC}"
echo "• View ACR: az acr repository list --name $ACR_NAME --output table"
echo "• View containers: az container list --resource-group $RESOURCE_GROUP --output table"
echo "• Delete everything: az group delete --name $RESOURCE_GROUP --yes --no-wait"