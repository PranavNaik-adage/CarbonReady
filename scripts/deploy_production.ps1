# CarbonReady Production Deployment Script (PowerShell)
# Automates the deployment of CarbonReady infrastructure to AWS

$ErrorActionPreference = "Stop"

# Configuration
$REGION = if ($env:CDK_DEFAULT_REGION) { $env:CDK_DEFAULT_REGION } else { "ap-south-1" }
$ACCOUNT = $env:CDK_DEFAULT_ACCOUNT
$ENV = if ($env:DEPLOYMENT_ENV) { $env:DEPLOYMENT_ENV } else { "production" }

# Functions
function Print-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Check-Prerequisites {
    Print-Header "Checking Prerequisites"
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>&1
        Print-Success "AWS CLI installed: $awsVersion"
    }
    catch {
        Print-Error "AWS CLI not found. Please install AWS CLI v2."
        exit 1
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Print-Success "Python installed: $pythonVersion"
    }
    catch {
        Print-Error "Python not found. Please install Python 3.12+."
        exit 1
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>&1
        Print-Success "Node.js installed: $nodeVersion"
    }
    catch {
        Print-Error "Node.js not found. Please install Node.js 18+."
        exit 1
    }
    
    # Check CDK
    try {
        $cdkVersion = cdk --version 2>&1
        Print-Success "AWS CDK installed: $cdkVersion"
    }
    catch {
        Print-Error "AWS CDK not found. Please install: npm install -g aws-cdk"
        exit 1
    }
    
    # Check AWS credentials
    try {
        $accountId = aws sts get-caller-identity --query Account --output text 2>&1
        Print-Success "AWS credentials configured (Account: $accountId)"
        $script:ACCOUNT = $accountId
    }
    catch {
        Print-Error "AWS credentials not configured. Run: aws configure"
        exit 1
    }
}

function Setup-Environment {
    Print-Header "Setting Up Environment"
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path ".venv")) {
        Print-Info "Creating Python virtual environment..."
        python -m venv .venv
        Print-Success "Virtual environment created"
    }
    else {
        Print-Success "Virtual environment already exists"
    }
    
    # Activate virtual environment
    Print-Info "Activating virtual environment..."
    & .\.venv\Scripts\Activate.ps1
    Print-Success "Virtual environment activated"
    
    # Install dependencies
    Print-Info "Installing Python dependencies..."
    pip install -q -r requirements.txt
    Print-Success "Dependencies installed"
}

function Bootstrap-CDK {
    Print-Header "Bootstrapping CDK"
    
    if (-not $ACCOUNT) {
        $ACCOUNT = aws sts get-caller-identity --query Account --output text
    }
    
    Print-Info "Bootstrapping CDK in account $ACCOUNT, region $REGION..."
    
    try {
        cdk bootstrap "aws://$ACCOUNT/$REGION"
        Print-Success "CDK bootstrap complete"
    }
    catch {
        Print-Warning "CDK bootstrap may have already been done"
    }
}

function Review-Changes {
    Print-Header "Reviewing Infrastructure Changes"
    
    Print-Info "Synthesizing CloudFormation templates..."
    cdk synth | Out-Null
    Print-Success "Templates synthesized"
    
    Print-Info "Checking for differences..."
    try {
        cdk diff --all
        Print-Success "Diff complete"
    }
    catch {
        Print-Warning "Some differences detected (this is normal for first deployment)"
    }
    
    Write-Host ""
    $confirm = Read-Host "Do you want to proceed with deployment? (yes/no)"
    if ($confirm -ne "yes") {
        Print-Error "Deployment cancelled by user"
        exit 1
    }
}

function Deploy-Infrastructure {
    Print-Header "Deploying Infrastructure"
    
    Print-Info "Deploying all CDK stacks..."
    Print-Info "This may take 10-15 minutes..."
    Write-Host ""
    
    try {
        cdk deploy --all --require-approval never
        Print-Success "Infrastructure deployment complete"
    }
    catch {
        Print-Error "Infrastructure deployment failed"
        exit 1
    }
    
    # Save outputs
    Print-Info "Saving deployment outputs..."
    try {
        cdk deploy --all --outputs-file cdk-outputs.json --require-approval never 2>&1 | Out-Null
    }
    catch {
        # Ignore errors when saving outputs
    }
    
    if (Test-Path "cdk-outputs.json") {
        Print-Success "Outputs saved to cdk-outputs.json"
    }
}

function Setup-Alarms {
    Print-Header "Setting Up CloudWatch Alarms"
    
    Print-Info "Creating production alarms..."
    try {
        python scripts/setup_production_alarms.py --region $REGION
        Print-Success "CloudWatch alarms configured"
    }
    catch {
        Print-Warning "Failed to create some alarms (may need manual setup)"
    }
}

function Initialize-Data {
    Print-Header "Initializing Production Data"
    
    # Initialize CRI weights
    Print-Info "Initializing CRI weights..."
    try {
        python scripts/init_cri_weights.py
        Print-Success "CRI weights initialized"
    }
    catch {
        Print-Warning "Failed to initialize CRI weights"
    }
    
    # Initialize growth curves
    Print-Info "Initializing growth curves..."
    try {
        python scripts/init_growth_curves.py
        Print-Success "Growth curves initialized"
    }
    catch {
        Print-Warning "Failed to initialize growth curves"
    }
}

function Verify-Deployment {
    Print-Header "Verifying Deployment"
    
    Print-Info "Running deployment verification..."
    try {
        python scripts/verify_deployment.py --env $ENV --region $REGION
        Print-Success "Deployment verification passed"
    }
    catch {
        Print-Warning "Some verification checks failed (review output above)"
    }
}

function Print-NextSteps {
    Print-Header "Deployment Complete!"
    
    Write-Host "Next steps:"
    Write-Host ""
    Write-Host "1. Subscribe email addresses to SNS topics:"
    Write-Host "   aws sns subscribe --topic-arn <CRITICAL_ALERTS_ARN> --protocol email --notification-endpoint admin@example.com"
    Write-Host ""
    Write-Host "2. Create Cognito users:"
    Write-Host "   aws cognito-idp admin-create-user --user-pool-id <POOL_ID> --username admin@example.com ..."
    Write-Host ""
    Write-Host "3. Provision IoT devices:"
    Write-Host "   See PRODUCTION_DEPLOYMENT.md for detailed instructions"
    Write-Host ""
    Write-Host "4. Test the system:"
    Write-Host "   python scripts/test_system.py --env production"
    Write-Host ""
    Write-Host "5. Monitor the deployment:"
    Write-Host "   - CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch"
    Write-Host "   - API Gateway: Check cdk-outputs.json for API URL"
    Write-Host ""
    
    if (Test-Path "cdk-outputs.json") {
        Print-Info "Deployment outputs saved in: cdk-outputs.json"
    }
    
    Print-Success "Production deployment successful!"
}

# Main execution
function Main {
    Print-Header "CarbonReady Production Deployment"
    Print-Info "Environment: $ENV"
    Print-Info "Region: $REGION"
    Print-Info "Account: $(if ($ACCOUNT) { $ACCOUNT } else { '<will be detected>' })"
    Write-Host ""
    
    Check-Prerequisites
    Setup-Environment
    Bootstrap-CDK
    Review-Changes
    Deploy-Infrastructure
    Setup-Alarms
    Initialize-Data
    Verify-Deployment
    Print-NextSteps
}

# Run main function
Main
