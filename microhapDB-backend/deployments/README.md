# 🚀 MicrohapDB Backend Deployment

This directory contains deployment scripts and configurations for the MicrohapDB backend.

## 📋 Available Deployment Methods

### 🖥️ **AWS EC2 (Recommended)**
- **Script**: `deploy-to-ec2.sh`
- **Update Script**: `update-deployment.sh`
- **Status**: ✅ **Production Ready**
- **Cost**: ~$8-15/month (t3.micro)
- **Features**: 
  - Docker containerized deployment
  - Automatic health checks
  - Easy updates and rollbacks
  - Production-grade logging

### 🤖 **GitHub Actions (Automated)**
- **Workflow**: `.github/workflows/deploy.yml`
- **Status**: ✅ **Production Ready**
- **Features**:
  - Automated deployment on push to main
  - Docker build and push to GHCR
  - Automatic EC2 deployment
  - Health checks and rollback

## 🎯 **Recommended Deployment Flow**

### **Initial Setup**
```bash
# 1. Deploy infrastructure
cd microhapDB-backend/deployments
./deploy-to-ec2.sh

# 2. Set up GitHub Actions (optional but recommended)
# Follow GITHUB_ACTIONS_SETUP.md
```

### **Updates**
```bash
# Option 1: Manual update
./update-deployment.sh

# Option 2: Automatic via GitHub Actions
git push origin main  # Triggers automatic deployment
```

## 📁 **File Structure**

```
deployments/
├── README.md                 # This file
├── deploy-to-ec2.sh         # Initial EC2 deployment
└── update-deployment.sh     # Update existing deployment
```

## 🔧 **Prerequisites**

- AWS CLI configured with appropriate permissions
- Docker installed (for local testing)
- SSH key pair for EC2 access

## 📊 **Deployment Comparison**

| Method | Setup Time | Automation | Cost | Maintenance |
|--------|------------|------------|------|-------------|
| **EC2 Manual** | 15 min | Manual | $8-15/month | Low |
| **GitHub Actions** | 30 min | Full | $8-15/month | Minimal |

## 🆘 **Troubleshooting**

### **Common Issues**

1. **Permission Denied**
   ```bash
   # Fix script permissions
   chmod +x deploy-to-ec2.sh
   chmod +x update-deployment.sh
   ```

2. **AWS Credentials**
   ```bash
   # Configure AWS CLI
   aws configure
   ```

3. **Docker Issues**
   ```bash
   # Check Docker status on EC2
   ssh -i your-key.pem ec2-user@your-instance-ip
   sudo docker ps
   sudo docker logs microhapdb-backend
   ```

4. **Health Check Failures**
   ```bash
   # Check backend logs
   curl http://your-instance-ip/health
   ```

## 🔗 **Related Documentation**

- `GITHUB_ACTIONS_SETUP.md` - GitHub Actions configuration
- `TERRAFORM_INTEGRATION_GUIDE.md` - Infrastructure as Code
- `../TROUBLESHOOTING.md` - Backend troubleshooting

## 🎉 **Success Indicators**

✅ **Deployment Successful When:**
- Health endpoint returns 200: `http://your-instance-ip/health`
- API documentation accessible: `http://your-instance-ip/docs`
- Database connection working
- ORCID authentication functional

Your backend is now running in production! 🌟 