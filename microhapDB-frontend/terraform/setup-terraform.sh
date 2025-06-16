#!/bin/bash

# 🏗️ Terraform Setup Script for MicrohapDB Frontend
# This script helps you get started with Terraform infrastructure management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "main.tf" ]]; then
    print_error "Please run this script from the microhapDB-frontend/terraform directory"
    exit 1
fi

print_status "🏗️ MicrohapDB Frontend Terraform Setup"
echo "========================================"

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed!"
    echo ""
    echo "Install Terraform:"
    echo "  macOS: brew install terraform"
    echo "  Other: https://www.terraform.io/downloads"
    exit 1
fi

print_success "✅ Terraform is installed: $(terraform version -json | jq -r '.terraform_version')"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI is not configured or credentials are invalid"
    echo ""
    echo "Configure AWS CLI:"
    echo "  aws configure"
    echo "  Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-2")
print_success "✅ AWS configured - Account: $AWS_ACCOUNT, Region: $AWS_REGION"

# Create terraform.tfvars if it doesn't exist
if [[ ! -f "terraform.tfvars" ]]; then
    print_status "📝 Creating terraform.tfvars from example..."
    cp terraform.tfvars.example terraform.tfvars
    
    # Get backend URL from user
    echo ""
    read -p "Enter your backend URL (default: http://18.117.136.223): " BACKEND_URL
    BACKEND_URL=${BACKEND_URL:-"http://18.117.136.223"}
    
    # Update terraform.tfvars
    sed -i.bak "s|backend_url = \".*\"|backend_url = \"$BACKEND_URL\"|" terraform.tfvars
    rm terraform.tfvars.bak
    
    print_success "✅ Created terraform.tfvars"
    print_warning "⚠️  Please review and customize terraform.tfvars before proceeding"
    echo ""
    echo "Key settings to review:"
    echo "  - project_name: Affects resource naming"
    echo "  - environment: Used for tagging"
    echo "  - backend_url: Your API endpoint"
    echo ""
    read -p "Press Enter to continue after reviewing terraform.tfvars..."
fi

# Initialize Terraform
print_status "🚀 Initializing Terraform..."
if terraform init; then
    print_success "✅ Terraform initialized"
else
    print_error "❌ Terraform initialization failed"
    exit 1
fi

# Validate configuration
print_status "🔍 Validating Terraform configuration..."
if terraform validate; then
    print_success "✅ Configuration is valid"
else
    print_error "❌ Configuration validation failed"
    exit 1
fi

# Format code
print_status "🎨 Formatting Terraform code..."
terraform fmt

# Show plan
print_status "📋 Generating Terraform plan..."
echo ""
print_warning "⚠️  This will show what resources will be created in AWS"
echo ""
read -p "Continue with terraform plan? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if terraform plan -out=tfplan; then
        print_success "✅ Plan generated successfully"
        echo ""
        echo "Plan saved to: tfplan"
        echo ""
        print_status "📊 Plan Summary:"
        terraform show -json tfplan | jq -r '.planned_values.root_module.resources[] | "  + \(.type).\(.name)"' 2>/dev/null || echo "  (Install jq for detailed summary)"
    else
        print_error "❌ Plan generation failed"
        exit 1
    fi
else
    print_warning "⚠️  Skipping plan generation"
fi

# Ask about applying
echo ""
print_status "🎯 Next Steps:"
echo ""
echo "1. Review the plan above"
echo "2. Apply changes: terraform apply tfplan"
echo "3. Get outputs: terraform output"
echo "4. Update GitHub secrets with the outputs"
echo ""
print_warning "⚠️  This will create real AWS resources that may incur costs (~$0.11/month)"
echo ""
read -p "Apply the Terraform plan now? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "🚀 Applying Terraform plan..."
    if terraform apply tfplan; then
        print_success "🎉 Infrastructure deployed successfully!"
        echo ""
        print_status "📤 Terraform Outputs:"
        terraform output
        echo ""
        print_status "🔑 GitHub Secrets needed:"
        terraform output github_secrets
        echo ""
        print_success "✅ Setup complete!"
        echo ""
        echo "Next steps:"
        echo "1. Add the GitHub secrets shown above to your repository"
        echo "2. Update your GitHub Actions workflow to use the new resources"
        echo "3. Test your deployment"
    else
        print_error "❌ Terraform apply failed"
        exit 1
    fi
else
    print_status "ℹ️  Terraform plan saved to 'tfplan'"
    echo ""
    echo "To apply later:"
    echo "  terraform apply tfplan"
    echo ""
    echo "To destroy resources:"
    echo "  terraform destroy"
fi

print_success "🎉 Terraform setup complete!" 