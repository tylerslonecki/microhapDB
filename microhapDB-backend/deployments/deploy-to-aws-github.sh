#!/bin/bash

# AWS ECS Deployment Script for MicrohapDB Backend (using GitHub Container Registry)
set -e

# Configuration
AWS_REGION="us-east-2"
GITHUB_USERNAME="your-github-username"  # Replace with your GitHub username
GITHUB_REPOSITORY="microhap-backend"
ECS_CLUSTER="microhap-cluster"
ECS_SERVICE="microhap-backend-service"
TASK_DEFINITION="microhap-backend-task"

echo "Starting deployment process with GitHub Container Registry..."

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

# Build Docker image
echo "Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Tag image with latest
echo "Tagging image..."
docker tag $DOCKER_IMAGE:latest $DOCKER_IMAGE:latest

# Login to GitHub Container Registry
echo "Logging into GitHub Container Registry..."
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Push image to GitHub Container Registry
echo "Pushing image to GitHub Container Registry..."
docker push $DOCKER_IMAGE:latest

# Update ECS task definition with new image
echo "Creating new ECS task definition..."
aws ecs describe-task-definition --task-definition $TASK_DEFINITION --region $AWS_REGION --query taskDefinition > task-def.json

# Update the image in task definition
sed -i.bak "s|\"image\":.*|\"image\": \"${DOCKER_IMAGE}:latest\",|g" task-def.json

# Remove unnecessary fields for new task definition
jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .registeredAt, .registeredBy, .placementConstraints, .compatibilities)' task-def.json > task-def-new.json

# Register new task definition
echo "Registering new task definition..."
aws ecs register-task-definition --cli-input-json file://task-def-new.json --region $AWS_REGION

# Clean up temporary files
rm task-def.json task-def.json.bak task-def-new.json

# Update ECS service with new task definition
echo "Updating ECS service..."
aws ecs update-service \
    --cluster $ECS_CLUSTER \
    --service $ECS_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION

echo "Deployment completed successfully!"
echo "Your backend container is now publicly available at: https://github.com/${GITHUB_USERNAME}/${GITHUB_REPOSITORY}/pkgs/container/${GITHUB_REPOSITORY}"
echo "ECS service is updating with the new image..." 