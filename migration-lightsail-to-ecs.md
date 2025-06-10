# Migration Guide: Lightsail → ECS

When you're ready to scale from Lightsail to ECS, this guide will walk you through the migration process with **zero downtime** and minimal changes.

## When to Migrate

Consider migrating when you need:
- ✅ **Auto-scaling** based on traffic
- ✅ **High availability** across multiple AZs
- ✅ **Advanced monitoring** and alerting
- ✅ **Multiple environments** (dev/staging/prod)
- ✅ **Team access control** with IAM roles
- ✅ **Production-grade** infrastructure

## Migration Overview

### What Stays the Same:
✅ **Container images** (same GitHub CR images)  
✅ **Database** (same RDS instance)  
✅ **Frontend** (same S3 + CloudFront)  
✅ **Application code** (no changes)  
✅ **GitHub Container Registry** (no registry changes)  

### What Changes:
🔄 **Infrastructure**: VPC, ALB, ECS replaces Lightsail  
🔄 **Cost**: ~$30-34/month instead of $11-23/month  
🔄 **Management**: Terraform instead of simple commands  

## Step-by-Step Migration

### Phase 1: Prepare ECS Infrastructure

1. **Ensure you have your GitHub username ready**:
   ```bash
   # You should already have this from Lightsail
   echo $GITHUB_TOKEN
   ```

2. **Create Terraform configuration**:
   ```bash
   # In your project root, create terraform.tfvars
   cat > terraform.tfvars << EOF
   github_username = "your-github-username"  # Same as Lightsail
   project_name = "microhap"
   aws_region = "us-east-2"
   EOF
   ```

3. **Deploy ECS infrastructure**:
   ```bash
   terraform init
   terraform plan  # Review what will be created
   terraform apply
   ```

   This creates the ECS infrastructure **alongside** your existing Lightsail (no impact).

### Phase 2: Deploy to ECS

1. **Get the container image URL from your current Lightsail**:
   ```bash
   # This should match what ECS will use
   terraform output container_image
   # Should show: ghcr.io/your-username/microhap-backend:latest
   ```

2. **Deploy your container to ECS**:
   ```bash
   cd microhapDB-backend
   # Your existing GitHub deployment script works with ECS too!
   ./deployments/deploy-to-aws-github.sh
   ```

3. **Get your new ECS backend URL**:
   ```bash
   terraform output backend_url
   # Example: http://microhap-alb-1234567890.us-east-2.elb.amazonaws.com
   ```

### Phase 3: Test ECS Deployment

1. **Test the ECS backend directly**:
   ```bash
   # Replace with your actual ECS URL
   curl http://your-ecs-alb-url/docs
   ```

2. **Test database connectivity**:
   ```bash
   # Your ECS backend should connect to the same RDS as Lightsail
   curl http://your-ecs-alb-url/health  # If you have a health endpoint
   ```

### Phase 4: Switch Frontend

1. **Update frontend configuration**:
   ```bash
   cd microhapDB-frontend
   # Update your API base URL to point to ECS ALB
   # In your frontend config file (src/config/api.js or similar):
   # const API_BASE_URL = 'http://your-ecs-alb-url'
   ```

2. **Redeploy frontend**:
   ```bash
   npm run build
   aws s3 sync ./dist s3://your-s3-bucket --delete
   
   # Invalidate CloudFront cache
   aws cloudfront create-invalidation \
     --distribution-id your-distribution-id \
     --paths "/*"
   ```

3. **Test the complete application**:
   - Frontend should now talk to ECS backend
   - Authentication should work the same
   - Database operations should work the same

### Phase 5: Cleanup Lightsail

**Only after confirming ECS works perfectly:**

1. **Stop Lightsail service**:
   ```bash
   aws lightsail update-container-service \
     --service-name microhap-backend \
     --scale 0 \
     --region us-east-2
   ```

2. **Test application still works** (should use ECS now)

3. **Delete Lightsail service** (after 24-48 hours of successful ECS operation):
   ```bash
   aws lightsail delete-container-service \
     --service-name microhap-backend \
     --region us-east-2
   ```

## Zero-Downtime Migration Strategy

To ensure **zero downtime** during migration:

1. **Keep Lightsail running** while setting up ECS
2. **Deploy ECS in parallel** (different URLs)
3. **Test ECS thoroughly** before switching
4. **Switch frontend atomically** (single CloudFront invalidation)
5. **Keep Lightsail as backup** for 24-48 hours
6. **Cleanup only after confirmation**

## Cost Comparison During Migration

| Phase | Lightsail | ECS | Total |
|-------|-----------|-----|-------|
| **Before Migration** | $11-23/month | $0 | $11-23/month |
| **During Migration** | $11-23/month | $30-34/month | $41-57/month |
| **After Migration** | $0 | $30-34/month | $30-34/month |

**Migration period**: Usually 1-7 days of dual costs.

## Rollback Plan

If something goes wrong with ECS:

1. **Switch frontend back** to Lightsail URL
2. **Scale Lightsail back up**:
   ```bash
   aws lightsail update-container-service \
     --service-name microhap-backend \
     --scale 1 \
     --region us-east-2
   ```
3. **Redeploy frontend** with Lightsail URL
4. **Debug ECS issues** without pressure

## Migration Checklist

### Pre-Migration:
- [ ] Lightsail working perfectly
- [ ] GitHub Container Registry set up
- [ ] AWS CLI configured
- [ ] Terraform installed
- [ ] Frontend code can handle URL changes

### During Migration:
- [ ] ECS infrastructure deployed
- [ ] Container deployed to ECS
- [ ] ECS backend tested independently
- [ ] Frontend updated to use ECS
- [ ] End-to-end testing complete
- [ ] Performance testing done

### Post-Migration:
- [ ] Application stable for 24-48 hours
- [ ] Monitoring set up (CloudWatch)
- [ ] Lightsail cleaned up
- [ ] Documentation updated
- [ ] Team notified of new URLs

## Advanced ECS Features to Enable

After successful migration, consider adding:

### Auto-Scaling:
```bash
# Enable auto-scaling based on CPU/memory
aws ecs put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/microhap-cluster/microhap-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling
```

### CloudWatch Monitoring:
```bash
# Set up CloudWatch alarms for your ECS service
aws cloudwatch put-metric-alarm \
  --alarm-name "microhap-cpu-high" \
  --alarm-description "CPU utilization too high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

### Multiple Environments:
```bash
# Use Terraform workspaces for dev/staging/prod
terraform workspace new staging
terraform workspace new production
```

## Migration Timeline

**Typical migration timeline:**

| Day | Task | Duration |
|-----|------|----------|
| **Day 1** | Deploy ECS infrastructure | 1-2 hours |
| **Day 2** | Deploy container to ECS | 30 minutes |
| **Day 3** | Test ECS thoroughly | 2-4 hours |
| **Day 4** | Switch frontend | 30 minutes |
| **Day 5-7** | Monitor stability | Ongoing |
| **Day 7+** | Cleanup Lightsail | 15 minutes |

**Total effort**: ~6-10 hours spread over a week.

## Support

If you encounter issues during migration:

1. **Check ECS service status**:
   ```bash
   aws ecs describe-services --cluster microhap-cluster --services microhap-backend-service
   ```

2. **View ECS logs**:
   ```bash
   aws logs tail /ecs/microhap-backend --follow
   ```

3. **Compare configurations**: Ensure ECS environment variables match Lightsail

4. **Test incrementally**: Don't change everything at once

The migration is designed to be **low-risk** and **reversible** - you can always go back to Lightsail if needed! 