#!/bin/bash

# AWS ECS Deployment Script for MicrohapDB Backend (using Docker Hub)
set -e

# Configuration
AWS_REGION="us-east-2"
DOCKER_HUB_USERNAME="your-dockerhub-username"  # Replace with your Docker Hub username
DOCKER_HUB_REPOSITORY="microhap-backend"
ECS_CLUSTER="microhap-cluster"
ECS_SERVICE="microhap-backend-service"
TASK_DEFINITION="microhap-backend-task"

echo "Starting deployment process with Docker Hub..."

# Check if Docker Hub username is set
if [ "$DOCKER_HUB_USERNAME" = "your-dockerhub-username" ]; then
    echo "⚠️  Please update DOCKER_HUB_USERNAME in this script with your actual Docker Hub username"
    exit 1
fi

DOCKER_IMAGE="${DOCKER_HUB_USERNAME}/${DOCKER_HUB_REPOSITORY}"

echo "Docker Hub Image: $DOCKER_IMAGE"

# Build Docker image
echo "Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Tag image with latest
echo "Tagging image..."
docker tag $DOCKER_IMAGE:latest $DOCKER_IMAGE:latest

# Login to Docker Hub (you'll be prompted for credentials)
echo "Logging into Docker Hub..."
echo "Please enter your Docker Hub credentials when prompted:"
docker login

# Push image to Docker Hub
echo "Pushing image to Docker Hub..."
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
echo "Your backend container is now publicly available at: https://hub.docker.com/r/${DOCKER_HUB_USERNAME}/${DOCKER_HUB_REPOSITORY}"
echo "ECS service is updating with the new image..." 