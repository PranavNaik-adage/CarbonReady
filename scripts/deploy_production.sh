#!/bin/bash
# CarbonReady Production Deployment Script
# Automates the deployment of CarbonReady infrastructure to AWS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="${CDK_DEFAULT_REGION:-ap-south-1}"
ACCOUNT="${CDK_DEFAULT_ACCOUNT}"
ENV="${DEPLOYMENT_ENV:-production}"

# Functions
print_header() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check AWS CLI
    if command -v aws &> /dev/null; then
        print_success "AWS CLI installed: $(aws --version)"
    else
        print_error "AWS CLI not found. Please install AWS CLI v2."
        exit 1
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python installed: $(python3 --version)"
    else
        print_error "Python 3 not found. Please install Python 3.12+."
        exit 1
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        print_success "Node.js installed: $(node --version)"
    else
        print_error "Node.js not found. Please install Node.js 18+."
        exit 1
    fi
    
    # Check CDK
    if command -v cdk &> /dev/null; then
        print_success "AWS CDK installed: $(cdk --version)"
    else
        print_error "AWS CDK not found. Please install: npm install -g aws-cdk"
        exit 1
    fi
    
    # Check AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        print_success "AWS credentials configured (Account: $ACCOUNT_ID)"
    else
        print_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi
}

setup_environment() {
    print_header "Setting Up Environment"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source .venv/bin/activate
    print_success "Virtual environment activated"
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -q -r requirements.txt
    print_success "Dependencies installed"
}

bootstrap_cdk() {
    print_header "Bootstrapping CDK"
    
    if [ -z "$ACCOUNT" ]; then
        ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    fi
    
    print_info "Bootstrapping CDK in account $ACCOUNT, region $REGION..."
    
    if cdk bootstrap aws://$ACCOUNT/$REGION; then
        print_success "CDK bootstrap complete"
    else
        print_warning "CDK bootstrap may have already been done"
    fi
}

review_changes() {
    print_header "Reviewing Infrastructure Changes"
    
    print_info "Synthesizing CloudFormation templates..."
    cdk synth > /dev/null
    print_success "Templates synthesized"
    
    print_info "Checking for differences..."
    if cdk diff --all; then
        print_success "Diff complete"
    else
        print_warning "Some differences detected (this is normal for first deployment)"
    fi
    
    echo ""
    read -p "Do you want to proceed with deployment? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_error "Deployment cancelled by user"
        exit 1
    fi
}

deploy_infrastructure() {
    print_header "Deploying Infrastructure"
    
    print_info "Deploying all CDK stacks..."
    print_info "This may take 10-15 minutes..."
    echo ""
    
    if cdk deploy --all --require-approval never; then
        print_success "Infrastructure deployment complete"
    else
        print_error "Infrastructure deployment failed"
        exit 1
    fi
    
    # Save outputs
    print_info "Saving deployment outputs..."
    cdk deploy --all --outputs-file cdk-outputs.json --require-approval never > /dev/null 2>&1 || true
    
    if [ -f "cdk-outputs.json" ]; then
        print_success "Outputs saved to cdk-outputs.json"
    fi
}

setup_alarms() {
    print_header "Setting Up CloudWatch Alarms"
    
    print_info "Creating production alarms..."
    if python3 scripts/setup_production_alarms.py --region $REGION; then
        print_success "CloudWatch alarms configured"
    else
        print_warning "Failed to create some alarms (may need manual setup)"
    fi
}

initialize_data() {
    print_header "Initializing Production Data"
    
    # Initialize CRI weights
    print_info "Initializing CRI weights..."
    if python3 scripts/init_cri_weights.py; then
        print_success "CRI weights initialized"
    else
        print_warning "Failed to initialize CRI weights"
    fi
    
    # Initialize growth curves
    print_info "Initializing growth curves..."
    if python3 scripts/init_growth_curves.py; then
        print_success "Growth curves initialized"
    else
        print_warning "Failed to initialize growth curves"
    fi
}

verify_deployment() {
    print_header "Verifying Deployment"
    
    print_info "Running deployment verification..."
    if python3 scripts/verify_deployment.py --env $ENV --region $REGION; then
        print_success "Deployment verification passed"
    else
        print_warning "Some verification checks failed (review output above)"
    fi
}

print_next_steps() {
    print_header "Deployment Complete!"
    
    echo "Next steps:"
    echo ""
    echo "1. Subscribe email addresses to SNS topics:"
    echo "   aws sns subscribe --topic-arn <CRITICAL_ALERTS_ARN> --protocol email --notification-endpoint admin@example.com"
    echo ""
    echo "2. Create Cognito users:"
    echo "   aws cognito-idp admin-create-user --user-pool-id <POOL_ID> --username admin@example.com ..."
    echo ""
    echo "3. Provision IoT devices:"
    echo "   See PRODUCTION_DEPLOYMENT.md for detailed instructions"
    echo ""
    echo "4. Test the system:"
    echo "   python3 scripts/test_system.py --env production"
    echo ""
    echo "5. Monitor the deployment:"
    echo "   - CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch"
    echo "   - API Gateway: Check cdk-outputs.json for API URL"
    echo ""
    
    if [ -f "cdk-outputs.json" ]; then
        print_info "Deployment outputs saved in: cdk-outputs.json"
    fi
    
    print_success "Production deployment successful!"
}

# Main execution
main() {
    print_header "CarbonReady Production Deployment"
    print_info "Environment: $ENV"
    print_info "Region: $REGION"
    print_info "Account: ${ACCOUNT:-<will be detected>}"
    echo ""
    
    check_prerequisites
    setup_environment
    bootstrap_cdk
    review_changes
    deploy_infrastructure
    setup_alarms
    initialize_data
    verify_deployment
    print_next_steps
}

# Run main function
main
