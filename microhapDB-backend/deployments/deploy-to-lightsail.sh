#!/bin/bash

# AWS Lightsail Deployment Script for MicrohapDB Backend (using GitHub Container Registry)
set -e

# Configuration
AWS_REGION="us-east-2"
GITHUB_USERNAME="your-github-username"  # Replace with your GitHub username
GITHUB_REPOSITORY="microhap-backend"
LIGHTSAIL_SERVICE="microhap-backend"
LIGHTSAIL_POWER="micro"  # micro ($10/month), small ($20/month), medium ($40/month)

echo "Starting Lightsail deployment with GitHub Container Registry..."

# Check if GitHub username is set
if [ "$GITHUB_USERNAME" = "your-github-username" ]; then
    echo "⚠️  Please update GITHUB_USERNAME in this script with your actual GitHub username"
    exit 1
fi

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  Please set GITHUB_TOKEN environment variable"
    echo "   Export your GitHub personal access token: export GITHUB_TOKEN=your_token"
    echo "   Token needs 'write:packages' permission"
    exit 1
fi

DOCKER_IMAGE="ghcr.io/${GITHUB_USERNAME}/${GITHUB_REPOSITORY}"

echo "GitHub Container Registry Image: $DOCKER_IMAGE"
echo "Lightsail Service: $LIGHTSAIL_SERVICE"
echo "Power: $LIGHTSAIL_POWER (~\$10-40/month depending on size)"

# Build Docker image
echo "Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Login to GitHub Container Registry
echo "Logging into GitHub Container Registry..."
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Push image to GitHub Container Registry
echo "Pushing image to GitHub Container Registry..."
docker push $DOCKER_IMAGE:latest

# Create Lightsail container service if it doesn't exist
echo "Creating/checking Lightsail container service..."
aws lightsail get-container-services --service-name $LIGHTSAIL_SERVICE --region $AWS_REGION 2>/dev/null || {
    echo "Creating new Lightsail container service..."
    aws lightsail create-container-service \
        --service-name $LIGHTSAIL_SERVICE \
        --power $LIGHTSAIL_POWER \
        --scale 1 \
        --region $AWS_REGION
    
    echo "⏳ Waiting for container service to be ready (this takes 3-5 minutes)..."
    while true; do
        STATE=$(aws lightsail get-container-services --service-name $LIGHTSAIL_SERVICE --region $AWS_REGION --query 'containerServices[0].state' --output text)
        if [ "$STATE" = "READY" ]; then
            echo "✅ Container service is ready!"
            break
        elif [ "$STATE" = "FAILED" ]; then
            echo "❌ Container service creation failed!"
            exit 1
        else
            echo "Current state: $STATE, waiting..."
            sleep 30
        fi
    done
}

# Create deployment configuration
echo "Creating deployment configuration..."
cat > lightsail-deployment.json << EOF
{
  "microhap-backend": {
    "image": "${DOCKER_IMAGE}:latest",
    "environment": {
      "DATABASE_URL": "postgresql://postgres:bipostgres@database-1.czwgjenckjul.us-east-2.rds.amazonaws.com:5432/haplosearch",
      "ENVIRONMENT": "production"
    },
    "ports": {
      "8000": "HTTP"
    }
  }
}
EOF

# Create public endpoint configuration
cat > lightsail-public-endpoint.json << EOF
{
  "containerName": "microhap-backend",
  "containerPort": 8000,
  "healthCheck": {
    "healthyThreshold": 2,
    "unhealthyThreshold": 2,
    "timeoutSeconds": 5,
    "intervalSeconds": 30,
    "path": "/docs",
    "successCodes": "200"
  }
}
EOF

# Deploy to Lightsail
echo "Deploying to Lightsail..."
aws lightsail create-container-service-deployment \
    --service-name $LIGHTSAIL_SERVICE \
    --containers file://lightsail-deployment.json \
    --public-endpoint file://lightsail-public-endpoint.json \
    --region $AWS_REGION

# Clean up temporary files
rm lightsail-deployment.json lightsail-public-endpoint.json

echo ""
echo "🎉 Deployment initiated successfully!"
echo ""
echo "📋 Service Details:"
echo "   Service Name: $LIGHTSAIL_SERVICE"
echo "   Region: $AWS_REGION"
echo "   Power: $LIGHTSAIL_POWER"
echo "   Container: $DOCKER_IMAGE:latest"
echo ""
echo "⏳ Deployment is in progress (takes 2-5 minutes)..."
echo ""
echo "📝 To check status:"
echo "   aws lightsail get-container-service-deployments --service-name $LIGHTSAIL_SERVICE --region $AWS_REGION"
echo ""
echo "🌐 To get the public URL:"
echo "   aws lightsail get-container-services --service-name $LIGHTSAIL_SERVICE --region $AWS_REGION --query 'containerServices[0].url' --output text"
echo ""
echo "💰 Estimated cost: ~\$10-40/month (depending on power level)"
echo "🔗 Your container is publicly available at: https://github.com/${GITHUB_USERNAME}/${GITHUB_REPOSITORY}/pkgs/container/${GITHUB_REPOSITORY}" 