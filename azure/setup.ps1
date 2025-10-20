# Azure Setup Script for FYP Stock Analyzer (PowerShell)
# This script sets up all required Azure resources for deployment

param(
    [string]$ResourceGroup = "fyp-stock-analyzer-rg",
    [string]$Location = "eastus",
    [string]$AcrName = "fypstockanalyzer"
)

# Colors for output
$Colors = @{
    Red = [ConsoleColor]::Red
    Green = [ConsoleColor]::Green
    Yellow = [ConsoleColor]::Yellow
    Blue = [ConsoleColor]::Blue
}

function Write-Step {
    param([string]$Message)
    Write-Host "Step: $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "Success: $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "Warning: $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "Error: $Message" -ForegroundColor $Colors.Red
}

Write-Host "FYP Stock Analyzer - Azure Setup" -ForegroundColor $Colors.Blue
Write-Host "================================================"

# Check if Azure CLI is installed
Write-Step "Checking Azure CLI installation..."
try {
    $null = az --version
    Write-Success "Azure CLI is installed"
} catch {
    Write-Error "Azure CLI is not installed. Please install it first:"
    Write-Host "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Login to Azure
Write-Step "Checking Azure login status..."
try {
    $null = az account show 2>$null
    Write-Success "Already logged into Azure"
} catch {
    Write-Warning "Not logged into Azure. Starting login process..."
    az login
}

# Get subscription ID
$SubscriptionId = (az account show --query id --output tsv)
Write-Success "Using subscription: $SubscriptionId"

# Create resource group
Write-Step "Creating resource group: $ResourceGroup"
az group create --name $ResourceGroup --location $Location --output table

Write-Success "Resource group created"

# Deploy Azure Container Registry
Write-Step "Deploying Azure Container Registry..."
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file azure/container-registry.json `
    --parameters registryName=$AcrName `
    --output table

Write-Success "Azure Container Registry deployed"

# Get ACR credentials
Write-Step "Getting ACR credentials..."
$AcrLoginServer = (az acr show --name $AcrName --resource-group $ResourceGroup --query loginServer --output tsv)
$AcrUsername = (az acr credential show --name $AcrName --resource-group $ResourceGroup --query username --output tsv)
$AcrPassword = (az acr credential show --name $AcrName --resource-group $ResourceGroup --query passwords[0].value --output tsv)

Write-Success "ACR Login Server: $AcrLoginServer"

# Create service principal for GitHub Actions
Write-Step "Creating service principal for GitHub Actions..."
$SpName = "fyp-github-actions-sp"
$SpJson = (az ad sp create-for-rbac `
    --name $SpName `
    --role contributor `
    --scopes "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup" `
    --sdk-auth)

Write-Success "Service principal created"

# Display GitHub Secrets
Write-Host ""
Write-Host "GitHub Secrets Configuration" -ForegroundColor $Colors.Yellow
Write-Host "================================================"
Write-Host "Add these secrets to your GitHub repository:"
Write-Host "Settings → Secrets and variables → Actions → New repository secret"
Write-Host ""
Write-Host "AZURE_CREDENTIALS:" -ForegroundColor $Colors.Green
Write-Host $SpJson
Write-Host ""
Write-Host "AZURE_RESOURCE_GROUP:" -ForegroundColor $Colors.Green -NoNewline
Write-Host " $ResourceGroup"
Write-Host "AZURE_REGISTRY_USERNAME:" -ForegroundColor $Colors.Green -NoNewline
Write-Host " $AcrUsername"
Write-Host "AZURE_REGISTRY_PASSWORD:" -ForegroundColor $Colors.Green -NoNewline
Write-Host " $AcrPassword"
Write-Host ""
Write-Host "STAGING_DATABASE_URL:" -ForegroundColor $Colors.Green -NoNewline
Write-Host " mongodb://admin:secure_password_123@localhost:27017/fyp_staging"
Write-Host "PRODUCTION_DATABASE_URL:" -ForegroundColor $Colors.Green -NoNewline
Write-Host " mongodb://admin:secure_password_123@localhost:27017/fyp_production"
Write-Host ""

# Save configuration to file
$ConfigFile = "azure-config.txt"
Write-Step "Saving configuration to $ConfigFile..."
$ConfigContent = @"
# Azure Configuration for FYP Stock Analyzer
# Generated on $(Get-Date)

Resource Group: $ResourceGroup
Location: $Location
ACR Name: $AcrName
ACR Login Server: $AcrLoginServer
Subscription ID: $SubscriptionId

# GitHub Secrets (copy these to GitHub):
AZURE_CREDENTIALS=$SpJson
AZURE_RESOURCE_GROUP=$ResourceGroup
AZURE_REGISTRY_USERNAME=$AcrUsername
AZURE_REGISTRY_PASSWORD=$AcrPassword
STAGING_DATABASE_URL=mongodb://admin:secure_password_123@localhost:27017/fyp_staging
PRODUCTION_DATABASE_URL=mongodb://admin:secure_password_123@localhost:27017/fyp_production
"@

$ConfigContent | Out-File -FilePath $ConfigFile -Encoding UTF8
Write-Success "Configuration saved to $ConfigFile"

Write-Host ""
Write-Host "Azure setup complete!" -ForegroundColor $Colors.Blue
Write-Host "================================================"
Write-Host "Next steps:"
Write-Host "1. Add the GitHub secrets shown above to your repository"
Write-Host "2. Push code to main branch to trigger CI/CD pipeline"
Write-Host "3. Monitor deployment in GitHub Actions"
Write-Host ""
Write-Host "Quick commands:" -ForegroundColor $Colors.Yellow
Write-Host "• View ACR: az acr repository list --name $AcrName --output table"
Write-Host "• View containers: az container list --resource-group $ResourceGroup --output table"
Write-Host "• Delete everything: az group delete --name $ResourceGroup --yes --no-wait"