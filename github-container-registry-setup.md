# Using GitHub Container Registry (ghcr.io) - Recommended

This guide explains how to use **GitHub Container Registry** as your container registry. It's **free for public repositories** and offers excellent integration with GitHub workflows and repositories.

## Why GitHub Container Registry?

✅ **Free for public repositories**  
✅ **Better GitHub integration** than Docker Hub  
✅ **Automatic package linking** to your repository  
✅ **Built-in CI/CD with GitHub Actions**  
✅ **Same security model** as your GitHub repository  

## Cost Comparison

| Service | Cost | Integration |
|---------|------|-------------|
| **AWS ECR** | ~$1/GB/month + data transfer | AWS native |
| **Docker Hub** | FREE (public) | Generic |
| **GitHub Container Registry** | **FREE (public)** | **Excellent GitHub integration** |

## Setup Steps

### 1. Create GitHub Personal Access Token

1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **"Generate new token (classic)"**
3. Select scopes:
   - ✅ `write:packages` (to push containers)
   - ✅ `read:packages` (to pull containers)
   - ✅ `delete:packages` (optional, to delete old versions)
4. Copy the token (you won't see it again!)
5. Save it securely

### 2. Set Environment Variable

```bash
export GITHUB_TOKEN=your_personal_access_token_here
```

**Make it permanent** by adding to your shell profile:
```bash
# Add to ~/.zshrc or ~/.bashrc
echo 'export GITHUB_TOKEN=your_personal_access_token_here' >> ~/.zshrc
source ~/.zshrc
```

### 3. Update Configuration

#### Option A: Use the GitHub-specific deployment script

1. Update `microhapDB-backend/deployments/deploy-to-aws-github.sh`:
   ```bash
   GITHUB_USERNAME="your-actual-github-username"
   ```

2. Run the GitHub deployment script:
   ```bash
   cd microhapDB-backend
   chmod +x deployments/deploy-to-aws-github.sh
   ./deployments/deploy-to-aws-github.sh
   ```

#### Option B: Update the existing Docker Hub script

Modify `microhapDB-backend/deployments/deploy-to-aws.sh`:
```bash
# Change these lines:
DOCKER_HUB_USERNAME="your-github-username"
DOCKER_HUB_REPOSITORY="microhap-backend"

# To:
DOCKER_IMAGE="ghcr.io/your-github-username/microhap-backend"

# And change the login command from:
docker login

# To:
echo $GITHUB_TOKEN | docker login ghcr.io -u your-github-username --password-stdin
```

### 4. Update Terraform Configuration

If using Terraform, create `terraform.tfvars`:
```hcl
docker_hub_username = "ghcr.io/your-github-username"
```

Or modify `aws-infrastructure.tf` directly:
```hcl
variable "github_username" {
  description = "GitHub username for container registry"
  type        = string
  default     = "your-github-username"
}

# In the ECS task definition:
image = "ghcr.io/${var.github_username}/microhap-backend:latest"
```

## Repository Package Settings

### Enable Package Visibility

1. Go to your **GitHub repository**
2. Push your first container (using the deployment script)
3. Go to **Packages** tab in your repository
4. Click on your package
5. Go to **Package settings**
6. Under **Danger Zone**, change visibility to **Public** (to keep it free)

### Link Package to Repository

GitHub should automatically link the package to your repository. If not:
1. Go to the package page
2. Click **"Connect repository"**
3. Select your repository

## Automated CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]
  workflow_dispatch:  # Allow manual triggering

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: microhap-backend

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository  
        uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ github.repository_owner }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            latest

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./microhapDB-backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-2

      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster microhap-cluster \
            --service microhap-backend-service \
            --force-new-deployment
```

### Required GitHub Secrets

Add these to your repository's **Settings** → **Secrets and variables** → **Actions**:

```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

## Manual Deployment Steps

### First Time Setup

1. **Create GitHub token** (steps above)
2. **Update deployment script** with your GitHub username
3. **Export GitHub token**:
   ```bash
   export GITHUB_TOKEN=your_token
   ```
4. **Run deployment**:
   ```bash
   cd microhapDB-backend
   ./deployments/deploy-to-aws-github.sh
   ```

### Subsequent Deployments

Just run the script - it will build, push, and update ECS automatically:
```bash
./deployments/deploy-to-aws-github.sh
```

## Security Benefits

✅ **Token-based authentication** (more secure than password)  
✅ **Scoped permissions** (only package access)  
✅ **Automatic expiration** options for tokens  
✅ **Audit logs** in GitHub  
✅ **Same security model** as your repository  

## Troubleshooting

### Authentication Issues

```bash
# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Test Docker login
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin
```

### Package Not Showing Up

1. Ensure package visibility is set to **Public**
2. Check if package is linked to repository
3. Verify GitHub token has `write:packages` permission

### ECS Pull Issues

GitHub Container Registry is public, so no special ECS configuration needed. Verify:
1. Image URL is correct: `ghcr.io/username/microhap-backend:latest`
2. Package is public
3. ECS has internet access

## Cost Comparison Summary

| Feature | GitHub CR | Docker Hub | ECR |
|---------|-----------|------------|-----|
| **Cost** | FREE | FREE | ~$10-50/month |
| **GitHub Integration** | Excellent | Basic | None |
| **CI/CD** | Built-in Actions | Third-party | CodePipeline |
| **Package Management** | Native | Basic | Advanced |
| **Security** | GitHub-native | Separate account | AWS IAM |

**Recommendation**: Use GitHub Container Registry if your code is on GitHub! 