# AWS Deployment Guide for MicrohapDB

This guide will help you deploy your MicrohapDB application (FastAPI backend + Vue.js frontend) to AWS, connecting to your existing RDS database.

## Architecture Overview

- **Backend**: FastAPI on AWS ECS Fargate with Application Load Balancer
- **Frontend**: Vue.js hosted on S3 with CloudFront CDN
- **Database**: Your existing AWS RDS PostgreSQL instance
- **Container Registry**: GitHub Container Registry (recommended) or Docker Hub

## 💰 Cost-Saving Alternative: Free Container Registries

**Use GitHub Container Registry or Docker Hub instead of ECR to eliminate container registry costs entirely!**

**Cost Comparison**:
- ECR: ~$10-50/month for registry + data transfer
- GitHub Container Registry: **FREE (public repositories)**
- Docker Hub: **FREE (public repositories)**
- **Savings: 100% on container registry costs**

## Quick Start Summary

### 🚀 Start Simple: Lightsail + GitHub CR (Recommended for Testing)

**Perfect for**: Quick authentication testing, learning, budget-conscious development

```bash
# 1. Set GitHub token
export GITHUB_TOKEN=your_personal_access_token

# 2. Deploy backend to Lightsail
cd microhapDB-backend
# Edit deploy-to-lightsail.sh to set your GitHub username
chmod +x deployments/deploy-to-lightsail.sh
./deployments/deploy-to-lightsail.sh

# 3. Get backend URL
aws lightsail get-container-services --service-name microhap-backend --region us-east-2 --query 'containerServices[0].url' --output text

# 4. Deploy frontend
cd ../microhapDB-frontend
# Update with backend URL from step 3
./deployments/deploy-to-aws.sh
```

**Cost**: ~$11-23/month | **Setup time**: ~15 minutes | **Migration**: Easy to ECS later

---

### 🏗️ Production-Ready: ECS + GitHub CR (When You Need More)

**Perfect for**: Production workloads, auto-scaling, team collaboration

```bash
# 1. Create terraform.tfvars
cat > terraform.tfvars << EOF
github_username = "your-github-username"
project_name = "microhap"
aws_region = "us-east-2"
EOF

# 2. Set GitHub token
export GITHUB_TOKEN=your_personal_access_token

# 3. Deploy infrastructure
terraform init && terraform apply

# 4. Deploy backend
cd microhapDB-backend
# Edit deploy-to-aws-github.sh to set your GitHub username
./deployments/deploy-to-aws-github.sh

# 5. Deploy frontend
cd ../microhapDB-frontend
# Update with backend URL from: terraform output backend_url
./deployments/deploy-to-aws.sh
```

**Cost**: ~$30-34/month | **Setup time**: ~2 hours | **Features**: Auto-scaling, HA, advanced monitoring

---

### 🐳 Alternative: Docker Hub (If Not Using GitHub)

```bash
# 1. Create terraform.tfvars
cat > terraform.tfvars << EOF
docker_hub_username = "your-dockerhub-username"
project_name = "microhap"  
aws_region = "us-east-2"
EOF

# 2. Deploy infrastructure
terraform init && terraform apply

# 3. Deploy backend
cd microhapDB-backend
# Edit deploy-to-aws.sh to set your Docker Hub username
./deployments/deploy-to-aws.sh

# 4. Deploy frontend  
cd ../microhapDB-frontend
./deployments/deploy-to-aws.sh
```

## Deployment Path Recommendation

```
📍 You are here
    ⬇️
🚀 Start with Lightsail (~$11-23/month)
    ⬇️ (When you need more features)
🏗️ Migrate to ECS (~$30-34/month)
    ⬇️ (For production scale)
⚡ Add auto-scaling, monitoring, etc.
```

## Detailed Instructions

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
   ```bash
   aws configure
   ```

2. **Docker installed** on your local machine

3. **GitHub account and Personal Access Token** (recommended)
   - Create token at: GitHub Settings → Developer settings → Personal access tokens
   - Required scopes: `write:packages`, `read:packages`
   - Alternative: Docker Hub account ([Sign up here](https://hub.docker.com))

4. **Terraform installed** (optional, for infrastructure as code)
   ```bash
   # macOS
   brew install terraform
   ```

5. **Node.js and npm** for frontend builds

## Deployment Options

### Option 1: Quick Deployment with Scripts (Recommended for Testing)

#### Step 1: Setup GitHub Container Registry (Recommended)

1. **Create GitHub Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Create token with `write:packages` and `read:packages` scopes
   - Save the token securely

2. **Set environment variable**:
   ```bash
   export GITHUB_TOKEN=your_personal_access_token
   
   # Make permanent
   echo 'export GITHUB_TOKEN=your_token' >> ~/.zshrc
   source ~/.zshrc
   ```

3. **Update deployment script**:
   ```bash
   # Edit microhapDB-backend/deployments/deploy-to-aws-github.sh
   GITHUB_USERNAME="your-actual-github-username"
   ```

**Alternative: Docker Hub Setup**
1. Create a free Docker Hub account at [hub.docker.com](https://hub.docker.com)
2. Update `microhapDB-backend/deployments/deploy-to-aws.sh`:
   ```bash
   DOCKER_HUB_USERNAME="your-actual-username"
   ```

#### Step 2: Deploy Backend to ECS

1. Navigate to the backend directory:
   ```bash
   cd microhapDB-backend
   ```

2. **For GitHub Container Registry** (recommended):
   ```bash
   chmod +x deployments/deploy-to-aws-github.sh
   ./deployments/deploy-to-aws-github.sh
   ```

   **For Docker Hub** (alternative):
   ```bash
   chmod +x deployments/deploy-to-aws.sh
   ./deployments/deploy-to-aws.sh
   ```

   **Note**: This script will fail initially because the ECS infrastructure doesn't exist yet. You need to create it first using Terraform (Option 2) or manually through AWS Console.

#### Step 3: Deploy Frontend to S3 + CloudFront

1. Navigate to the frontend directory:
   ```bash
   cd ../microhapDB-frontend
   ```

2. Update the API endpoint in your Vue.js app to point to your ECS backend URL (you'll get this from the ECS deployment)

3. Make the deployment script executable:
   ```bash
   chmod +x deployments/deploy-to-aws.sh
   ```

4. Run the deployment script:
   ```bash
   ./deployments/deploy-to-aws.sh
   ```

### Option 2: Infrastructure as Code with Terraform (Recommended for Production)

#### Step 1: Configure GitHub Container Registry

**Recommended**: Create `terraform.tfvars` to use GitHub Container Registry:
```hcl
github_username = "your-github-username"
project_name = "microhap"
aws_region = "us-east-2"
```

**Alternative**: For Docker Hub instead, use:
```hcl
docker_hub_username = "your-dockerhub-username"
project_name = "microhap"
aws_region = "us-east-2"
```

#### Step 2: Set Up GitHub Token (if using GitHub CR)

```bash
# Create GitHub Personal Access Token with 'write:packages' permission
export GITHUB_TOKEN=your_personal_access_token

# Make it permanent
echo 'export GITHUB_TOKEN=your_token' >> ~/.zshrc
source ~/.zshrc
```

#### Step 3: Deploy Infrastructure

1. From the project root directory:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

   This will create:
   - VPC with public subnets
   - ECS cluster and service configured for your container registry  
   - Application Load Balancer
   - S3 bucket for frontend
   - CloudFront distribution
   - Security groups and IAM roles

2. **Verify the container image** Terraform will use:
   ```bash
   terraform output container_image
   # Should show: ghcr.io/your-username/microhap-backend:latest
   ```

#### Step 4: Deploy Backend

1. **Update deployment script** with your GitHub username:
   ```bash
   # Edit microhapDB-backend/deployments/deploy-to-aws-github.sh
   GITHUB_USERNAME="your-actual-github-username"
   ```

2. **Deploy your backend**:
   ```bash
   cd microhapDB-backend
   chmod +x deployments/deploy-to-aws-github.sh
   ./deployments/deploy-to-aws-github.sh
   ```

   The script will:
   - Build your Docker image
   - Push to GitHub Container Registry (`ghcr.io/your-username/microhap-backend`)
   - Update ECS service to use the new image

#### Step 5: Deploy Frontend

1. Update your frontend API configuration with the backend URL from Terraform output:
   ```bash
   terraform output backend_url
   ```

2. Deploy frontend:
   ```bash
   cd ../microhapDB-frontend
   # Update S3_BUCKET in deploy-to-aws.sh with the bucket name from terraform output
   terraform output s3_bucket_name
   # Update CLOUDFRONT_DISTRIBUTION_ID with the distribution ID
   terraform output cloudfront_distribution_id
   ./deployments/deploy-to-aws.sh
   ```

#### Terraform Configuration Summary

Your `terraform.tfvars` should look like this:

```hcl
# GitHub Container Registry (Recommended)
github_username = "your-github-username"

# OR Docker Hub (Alternative)  
# docker_hub_username = "your-dockerhub-username"

# Project Configuration
project_name = "microhap"
aws_region = "us-east-2"
```

**Key Benefits of This Setup:**
- ✅ **Terraform manages all AWS infrastructure**
- ✅ **Container registry choice is configurable** 
- ✅ **GitHub CR integration** if your code is on GitHub
- ✅ **Infrastructure as Code** - version controlled and reproducible

## Manual AWS Console Setup (Alternative)

If you prefer using the AWS Console:

### Backend (ECS Setup)

1. **Create ECR Repository**:
   - Go to ECR in AWS Console
   - Create repository named "microhap-backend"

2. **Create ECS Cluster**:
   - Go to ECS → Clusters
   - Create cluster using Fargate

3. **Create Task Definition**:
   - Use the container image from ECR
   - Set CPU: 256, Memory: 512
   - Add environment variable: `DATABASE_URL` with your RDS connection string

4. **Create ECS Service**:
   - Use the task definition
   - Set desired count: 1
   - Create Application Load Balancer
   - Configure target group for port 8000

### Frontend (S3 + CloudFront Setup)

1. **Create S3 Bucket**:
   - Enable static website hosting
   - Set index document: `index.html`
   - Make bucket public

2. **Create CloudFront Distribution**:
   - Origin: Your S3 bucket website endpoint
   - Enable redirect HTTP to HTTPS
   - Set error pages to redirect 404s to `/index.html`

## Configuration Updates Needed

### Frontend API Configuration

Update your Vue.js frontend to point to the new backend URL. Look for API configuration files (typically in `src/config/` or environment variables) and update the backend URL.

Example:
```javascript
// src/config/api.js
const API_BASE_URL = 'http://your-alb-dns-name.us-east-2.elb.amazonaws.com'
```

### Backend Environment Variables

The backend is configured to use your existing RDS database. If you need to update the connection string or add other environment variables:

1. Update the ECS task definition
2. Add/modify environment variables
3. Redeploy the service

## Testing the Deployment

1. **Backend Health Check**:
   ```bash
   curl http://your-alb-dns-name/docs
   ```

2. **Frontend Access**:
   - S3: `http://your-bucket-name.s3-website-us-east-2.amazonaws.com`
   - CloudFront: `https://your-distribution-id.cloudfront.net`

## Cost Considerations

**Estimated monthly costs for low-traffic testing (with Docker Hub):**
- ECS Fargate (1 task): ~$15-20
- Application Load Balancer: ~$20
- S3 hosting: ~$1-5
- CloudFront: ~$1-10
- Container Registry (Docker Hub): **$0** (vs ~$10-50 for ECR)
- **Total: ~$37-55/month** (vs ~$47-105 with ECR)

**💡 Additional Cost-Saving Tips:**
- Use Docker Hub for container registry (FREE)
- Consider AWS Lightsail for simpler deployments (~$10-20/month total)
- Use AWS Free Tier where applicable
- Schedule ECS tasks to stop during non-testing hours

## Scaling and Production Considerations

1. **Enable HTTPS**: Get SSL certificate from ACM and configure on ALB
2. **Custom Domain**: Set up Route 53 for custom domain names
3. **Auto Scaling**: Configure ECS service auto scaling
4. **Monitoring**: Set up CloudWatch alarms and dashboards
5. **CI/CD**: Implement GitHub Actions or CodePipeline for automated deployments
6. **Security**: Use AWS Secrets Manager for database credentials
7. **Backup**: Configure RDS automated backups

## Troubleshooting

### Common Issues

1. **ECS Service Won't Start**:
   - Check CloudWatch logs: `/ecs/microhap-backend`
   - Verify security groups allow traffic on port 8000
   - Ensure ECR image exists and is accessible

2. **Frontend Can't Connect to Backend**:
   - Verify CORS configuration in FastAPI
   - Check that API URLs are correctly configured
   - Ensure ALB security group allows HTTP traffic

3. **Database Connection Issues**:
   - Verify RDS security group allows connections from ECS
   - Check database credentials and connection string
   - Ensure database is publicly accessible if ECS is in public subnets

### Useful Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster microhap-cluster --services microhap-backend-service

# View ECS logs
aws logs describe-log-streams --log-group-name /ecs/microhap-backend

# Update ECS service with new image
aws ecs update-service --cluster microhap-cluster --service microhap-backend-service --force-new-deployment

# CloudFront cache invalidation
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

## Next Steps

After successful deployment:

1. Test all authentication flows with the new URLs
2. Update any hardcoded URLs in your application
3. Set up monitoring and alerting
4. Configure backup strategies
5. Implement CI/CD pipeline for future deployments

## Support

For issues specific to:
- **AWS Services**: Check AWS documentation and CloudWatch logs
- **Application Issues**: Check application logs in CloudWatch
- **Terraform**: Run `terraform plan` to see what will change before applying 

## Detailed Instructions 