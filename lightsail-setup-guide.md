# AWS Lightsail Deployment Guide (Start Simple!)

Deploy your MicrohapDB backend to **AWS Lightsail** for quick, simple, and cost-effective testing. Perfect for getting started before migrating to ECS later.

## Why Start with Lightsail?

✅ **Faster setup**: ~15 minutes vs 2+ hours for ECS  
✅ **Lower cost**: $10-20/month vs $30-34/month  
✅ **Simpler**: No VPCs, security groups, or load balancers to configure  
✅ **Same containers**: Easy migration to ECS later  
✅ **GitHub CR compatible**: Still FREE container registry  

## Architecture

- **Backend**: FastAPI on Lightsail Container Service
- **Frontend**: S3 + CloudFront (same as ECS setup)
- **Database**: Your existing AWS RDS PostgreSQL
- **Container Registry**: GitHub Container Registry (FREE)

## Cost Breakdown

| Service | Lightsail | ECS Equivalent |
|---------|-----------|----------------|
| **Backend Container** | $10-40/month | $9/month (Fargate) |
| **Load Balancer** | Included | $20/month (ALB) |
| **Container Registry** | FREE (GitHub CR) | FREE (GitHub CR) |
| **Frontend (S3+CF)** | $1-3/month | $1-3/month |
| **Total** | **$11-43/month** | **$30-34/month** |

## Quick Start

### 1. Setup GitHub Container Registry

```bash
# Create GitHub Personal Access Token
# Go to: GitHub Settings → Developer settings → Personal access tokens
# Scopes: write:packages, read:packages

# Set environment variable
export GITHUB_TOKEN=your_personal_access_token

# Make it permanent
echo 'export GITHUB_TOKEN=your_token' >> ~/.zshrc
source ~/.zshrc
```

### 2. Configure and Deploy Backend

```bash
# 1. Navigate to backend directory
cd microhapDB-backend

# 2. Update deployment script
# Edit deployments/deploy-to-lightsail.sh:
GITHUB_USERNAME="your-actual-github-username"

# 3. Choose your power level (affects cost):
LIGHTSAIL_POWER="micro"   # $10/month - 512MB RAM, 0.25 vCPU
# LIGHTSAIL_POWER="small"  # $20/month - 1GB RAM, 0.5 vCPU  
# LIGHTSAIL_POWER="medium" # $40/month - 2GB RAM, 1 vCPU

# 4. Deploy!
chmod +x deployments/deploy-to-lightsail.sh
./deployments/deploy-to-lightsail.sh
```

### 3. Get Your Backend URL

```bash
# Get the public URL for your backend
aws lightsail get-container-services \
    --service-name microhap-backend \
    --region us-east-2 \
    --query 'containerServices[0].url' \
    --output text
```

### 4. Deploy Frontend (Same as ECS)

```bash
# Deploy frontend to S3 + CloudFront (same process as ECS)
cd ../microhapDB-frontend

# Update your frontend API configuration with the Lightsail backend URL
# Then deploy
chmod +x deployments/deploy-to-aws.sh
./deployments/deploy-to-aws.sh
```

## Lightsail Power Levels

| Power | RAM | vCPU | Cost/Month | Best For |
|-------|-----|------|------------|----------|
| **micro** | 512MB | 0.25 | $10 | Testing, light usage |
| **small** | 1GB | 0.5 | $20 | Small teams, dev work |
| **medium** | 2GB | 1 | $40 | Production-like testing |
| **large** | 4GB | 2 | $80 | Heavy usage |

**Recommendation**: Start with **micro** ($10/month) for testing authentication.

## Management Commands

### Check Service Status
```bash
aws lightsail get-container-services \
    --service-name microhap-backend \
    --region us-east-2
```

### View Deployment Status
```bash
aws lightsail get-container-service-deployments \
    --service-name microhap-backend \
    --region us-east-2
```

### Update Your Container
```bash
# Just run the deployment script again
./deployments/deploy-to-lightsail.sh
```

### Scale Up/Down
```bash
# Scale to 2 instances
aws lightsail update-container-service \
    --service-name microhap-backend \
    --scale 2 \
    --region us-east-2

# Scale back to 1
aws lightsail update-container-service \
    --service-name microhap-backend \
    --scale 1 \
    --region us-east-2
```

### Upgrade Power Level
```bash
# Upgrade from micro to small
aws lightsail update-container-service \
    --service-name microhap-backend \
    --power small \
    --region us-east-2
```

## Migration to ECS (When You're Ready)

When you outgrow Lightsail, migration to ECS is straightforward:

### What Stays the Same:
✅ **Container images** (same GitHub CR images)  
✅ **Database** (same RDS instance)  
✅ **Frontend** (same S3 + CloudFront)  
✅ **Application code** (no changes needed)  

### What Changes:
- **Infrastructure**: VPC, ALB, ECS instead of Lightsail
- **Cost**: ~$30-34/month instead of $10-20/month
- **Features**: Auto-scaling, multi-AZ, advanced monitoring

### Migration Steps:
1. **Deploy ECS infrastructure** using the existing Terraform
2. **Update ECS** to use same GitHub CR image
3. **Switch frontend** to point to ECS ALB URL
4. **Delete Lightsail service** once ECS is working

## When to Migrate to ECS

Consider migrating when you need:

| Feature | Lightsail | ECS |
|---------|-----------|-----|
| **Auto-scaling** | ❌ Manual | ✅ Automatic |
| **High Availability** | ❌ Single AZ | ✅ Multi-AZ |
| **Advanced Monitoring** | ❌ Basic | ✅ CloudWatch |
| **Multiple Environments** | ❌ Complex | ✅ Easy |
| **Team Access Control** | ❌ Limited | ✅ IAM roles |
| **Production Workloads** | ⚠️ Limited | ✅ Enterprise |

## Troubleshooting

### Container Won't Start
```bash
# Check deployment logs
aws lightsail get-container-service-deployments \
    --service-name microhap-backend \
    --region us-east-2

# Check service logs
aws lightsail get-container-log \
    --service-name microhap-backend \
    --container-name microhap-backend \
    --region us-east-2
```

### Database Connection Issues
- Lightsail containers run in public subnets
- Ensure your RDS security group allows connections from `0.0.0.0/0` (port 5432)
- Or create a security group specifically for Lightsail IP ranges

### GitHub CR Authentication
```bash
# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Test Docker login
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin
```

## Cost Optimization Tips

1. **Start with micro** power level ($10/month)
2. **Scale down when not testing**:
   ```bash
   aws lightsail update-container-service --service-name microhap-backend --scale 0
   ```
3. **Use GitHub CR** (FREE vs ECR costs)
4. **Monitor usage** and upgrade power only when needed

## Summary

**Lightsail is perfect for:**
- 🧪 **Quick authentication testing**
- 💰 **Budget-conscious development** 
- 🎓 **Learning cloud deployments**
- 🚀 **Getting started fast**

**Migration path ensures** you can scale up to ECS when your needs grow!

**Total setup time**: ~15 minutes  
**Total monthly cost**: ~$11-23 (including frontend)  
**Migration effort**: Minimal when ready 