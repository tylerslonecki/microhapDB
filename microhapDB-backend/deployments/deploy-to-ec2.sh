#!/bin/bash

# AWS EC2 Deployment Script for MicrohapDB Backend
set -e

###############################################################################
# PREREQUISITES
###############################################################################
# 1. AWS CLI configured with appropriate permissions (EC2, VPC)
# 2. Docker installed and running locally
# 3. GitHub Container Registry package set to PUBLIC visibility
#    Go to: https://github.com/[username]/microhapDB/pkgs/container/haplosearch
#    Settings → Change visibility → Public
# 4. Environment variables in .env file (DATABASE_URL, ORCID_*, GITHUB_TOKEN)
###############################################################################

###############################################################################
# Configuration
###############################################################################

# AWS & EC2
AWS_REGION="us-east-2"
INSTANCE_TYPE="t3.micro"  # Free tier eligible
KEY_NAME="microhapdb-key"  # SSH key name (will be created if doesn't exist)
SECURITY_GROUP_NAME="microhapdb-sg"
INSTANCE_NAME="microhapdb-backend"

# Docker / GitHub Container Registry
GITHUB_USERNAME="tylerslonecki"
IMAGE_NAME="haplosearch"
DOCKER_IMAGE="ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}"
CONTAINER_PORT=80

#-------------------------------------------------------------------------------
# Load environment variables from .env
#-------------------------------------------------------------------------------

# shellcheck disable=SC1090
load_env_file() {
  local file="$1"
  if [ -f "$file" ]; then
    echo "Loading environment variables from $file" >&2
    set -a
    source "$file"
    set +a
  fi
}

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd -- "$SCRIPT_DIR/.." && pwd )"

echo "[debug] Script directory: $SCRIPT_DIR"
echo "[debug] Project root: $PROJECT_ROOT"

# Load .env files
load_env_file "$PROJECT_ROOT/.env"

# Validate required variables
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${ORCID_CLIENT_ID:?ORCID_CLIENT_ID is required}"
: "${ORCID_CLIENT_SECRET:?ORCID_CLIENT_SECRET is required}"
: "${ORCID_REDIRECT_URI:?ORCID_REDIRECT_URI is required}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"

###############################################################################
# Deployment Functions
###############################################################################

echo "🚀 Starting EC2 deployment..."
echo "Instance Type: $INSTANCE_TYPE"
echo "Region: $AWS_REGION"
echo "Image: $DOCKER_IMAGE:latest"

# Build and push Docker image
echo ""
echo "📦 Building and pushing Docker image..."
echo "Building for AMD64 architecture (EC2 compatible)..."
docker buildx build --platform linux/amd64 -t "$DOCKER_IMAGE" -f "$PROJECT_ROOT/Dockerfile.simple" "$PROJECT_ROOT"

echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USERNAME" --password-stdin
docker push "$DOCKER_IMAGE:latest"

echo "✅ Docker image built and pushed successfully for AMD64 architecture"

# Get default VPC
echo ""
echo "🌐 Getting VPC information..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text --region "$AWS_REGION")
echo "VPC ID: $VPC_ID"

# Create security group
echo ""
echo "🔒 Setting up security group..."
SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' --output text --region "$AWS_REGION" 2>/dev/null)

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
    echo "Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SECURITY_GROUP_NAME" \
        --description "Security group for MicrohapDB backend" \
        --vpc-id "$VPC_ID" \
        --query 'GroupId' --output text --region "$AWS_REGION")
    
    # Allow SSH (port 22)
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp --port 22 --cidr 0.0.0.0/0 --region "$AWS_REGION"
    
    # Allow HTTP (port 80)
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp --port 80 --cidr 0.0.0.0/0 --region "$AWS_REGION"
    
    # Allow HTTPS (port 443)
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp --port 443 --cidr 0.0.0.0/0 --region "$AWS_REGION"
fi

echo "Security Group ID: $SG_ID"

# Create SSH key pair if it doesn't exist
echo ""
echo "🔑 Setting up SSH key pair..."
aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$AWS_REGION" >/dev/null 2>&1 || {
    echo "Creating SSH key pair..."
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' --output text --region "$AWS_REGION" > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    echo "SSH key saved as ${KEY_NAME}.pem"
}

# Get latest Amazon Linux 2 AMI
echo ""
echo "🖥️  Getting latest Amazon Linux 2 AMI..."
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text --region "$AWS_REGION")

echo "AMI ID: $AMI_ID"

# Create user data script
echo ""
echo "📝 Creating user data script..."
cat > user-data.sh << EOF
#!/bin/bash

# Log all output for debugging
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting user data script at \$(date)"

# Update system
echo "Updating system packages..."
yum update -y

# Install Docker
echo "Installing Docker..."
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
echo "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Wait for Docker to be ready
echo "Waiting for Docker to be ready..."
sleep 10

# Pull and run the container (public registry, no auth needed)
echo "Pulling Docker image..."
docker pull "$DOCKER_IMAGE:latest"

echo "Starting container..."
docker run -d \\
    --name microhapdb \\
    --restart unless-stopped \\
    -p 80:80 \\
    -e "DATABASE_URL=$DATABASE_URL" \\
    -e "ORCID_CLIENT_ID=$ORCID_CLIENT_ID" \\
    -e "ORCID_CLIENT_SECRET=$ORCID_CLIENT_SECRET" \\
    -e "ORCID_REDIRECT_URI=$ORCID_REDIRECT_URI" \\
    -e "ENVIRONMENT=production" \\
    "$DOCKER_IMAGE:latest"

# Wait for container to start
echo "Waiting for container to start..."
sleep 30

# Check container status
echo "Container status:"
docker ps -a

# Test health endpoint
echo "Testing health endpoint..."
curl -f http://localhost/health || echo "Health check failed, but container may still be starting"

# Create a simple health check script
cat > /home/ec2-user/health-check.sh << 'HEALTH_EOF'
#!/bin/bash
curl -f http://localhost/health || exit 1
HEALTH_EOF
chmod +x /home/ec2-user/health-check.sh

# Create a container management script
cat > /home/ec2-user/manage-container.sh << 'MANAGE_EOF'
#!/bin/bash
case "\$1" in
    start)
        docker start microhapdb
        ;;
    stop)
        docker stop microhapdb
        ;;
    restart)
        docker restart microhapdb
        ;;
    logs)
        docker logs microhapdb
        ;;
    status)
        docker ps -a | grep microhapdb
        ;;
    health)
        curl -f http://localhost/health
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart|logs|status|health}"
        exit 1
        ;;
esac
MANAGE_EOF
chmod +x /home/ec2-user/manage-container.sh

echo "User data script completed at \$(date)"
echo "Container should be running. Check with: docker ps"
echo "View logs with: docker logs microhapdb"
echo "Use /home/ec2-user/manage-container.sh for easy management"
EOF

# Launch EC2 instance
echo ""
echo "🚀 Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --count 1 \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data file://user-data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --query 'Instances[0].InstanceId' --output text --region "$AWS_REGION")

echo "Instance ID: $INSTANCE_ID"

# Wait for instance to be running
echo ""
echo "⏳ Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text --region "$AWS_REGION")

echo ""
echo "🎉 EC2 instance launched successfully!"
echo ""
echo "📋 Instance Details:"
echo "   Instance ID: $INSTANCE_ID"
echo "   Instance Type: $INSTANCE_TYPE"
echo "   Public IP: $PUBLIC_IP"
echo "   SSH Key: ${KEY_NAME}.pem"
echo ""
echo "🌐 Your application will be available at:"
echo "   http://$PUBLIC_IP"
echo "   http://$PUBLIC_IP/health"
echo "   http://$PUBLIC_IP/docs"
echo ""
echo "⏳ Waiting for application to start (this may take 2-3 minutes)..."

# Wait for the application to be ready
echo ""
echo "🔍 Testing deployment..."
RETRY_COUNT=0
MAX_RETRIES=12  # 12 * 15 seconds = 3 minutes

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Attempt $((RETRY_COUNT + 1))/$MAX_RETRIES: Testing health endpoint..."
    
    if curl -f -s "http://$PUBLIC_IP/health" > /dev/null 2>&1; then
        echo ""
        echo "✅ SUCCESS! Application is running and healthy!"
        echo ""
        echo "🧪 Testing endpoints:"
        echo "   Health Check:"
        curl -s "http://$PUBLIC_IP/health" | head -1
        echo ""
        echo "   Root Endpoint:"
        curl -s "http://$PUBLIC_IP/" 
        echo ""
        echo ""
        echo "🎯 Deployment completed successfully!"
        break
    else
        echo "   Not ready yet, waiting 15 seconds..."
        sleep 15
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo ""
    echo "⚠️  Application may still be starting. You can:"
    echo "   1. Wait a few more minutes and test manually: curl http://$PUBLIC_IP/health"
    echo "   2. SSH in to check logs: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
    echo "   3. Check container status: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP './manage-container.sh status'"
fi

echo ""
echo "📝 Useful commands:"
echo "   # SSH into the instance"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo ""
echo "   # Check container status"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP './manage-container.sh status'"
echo ""
echo "   # View container logs"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP './manage-container.sh logs'"
echo ""
echo "   # View deployment logs"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'sudo cat /var/log/user-data.log'"
echo ""
echo "   # Restart container"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP './manage-container.sh restart'"
echo ""
echo "   # Stop the instance (to save costs)"
echo "   aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "   # Terminate the instance (permanent)"
echo "   aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "💰 Estimated cost: ~\$8-15/month (t3.micro)"

# Clean up temporary files
rm -f user-data.sh 