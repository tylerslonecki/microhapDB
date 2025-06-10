#!/bin/bash

# AWS S3 + CloudFront Deployment Script for MicrohapDB Frontend
set -e

# Configuration
AWS_REGION="us-east-2"
S3_BUCKET="microhap-frontend-bucket"
CLOUDFRONT_DISTRIBUTION_ID=""  # Will be filled after CloudFront creation

echo "Starting frontend deployment process..."

# Build the Vue.js application
echo "Building Vue.js application..."
npm install
npm run build

# Create S3 bucket if it doesn't exist
echo "Creating S3 bucket if it doesn't exist..."
aws s3 mb s3://$S3_BUCKET --region $AWS_REGION || echo "Bucket already exists"

# Configure S3 bucket for static website hosting
echo "Configuring S3 bucket for static website hosting..."
aws s3 website s3://$S3_BUCKET --index-document index.html --error-document index.html

# Set bucket policy for public read access
echo "Setting bucket policy for public read access..."
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$S3_BUCKET/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $S3_BUCKET --policy file://bucket-policy.json
rm bucket-policy.json

# Sync built files to S3
echo "Uploading files to S3..."
aws s3 sync ./dist s3://$S3_BUCKET --delete

# If CloudFront distribution ID is provided, invalidate cache
if [ ! -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
fi

echo "Frontend deployment completed successfully!"
echo "Your frontend is now available at: http://$S3_BUCKET.s3-website-$AWS_REGION.amazonaws.com"
echo ""
echo "For production, consider setting up CloudFront distribution for better performance and HTTPS." 