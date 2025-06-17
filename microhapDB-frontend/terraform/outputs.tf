# Outputs for MicrohapDB Frontend Infrastructure

output "s3_bucket_name" {
  description = "Name of the S3 bucket hosting the frontend"
  value       = aws_s3_bucket.frontend.bucket
}

output "s3_bucket_website_endpoint" {
  description = "Website endpoint for the S3 bucket"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "website_url" {
  description = "Website URL (HTTPS)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.frontend.arn
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.arn
}

output "backend_cloudfront_distribution_id" {
  description = "Backend CloudFront distribution ID"
  value       = aws_cloudfront_distribution.backend_api.id
}

output "backend_cloudfront_domain_name" {
  description = "Backend CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.backend_api.domain_name
}

output "backend_api_url" {
  description = "Backend API URL (HTTPS via CloudFront)"
  value       = "https://${aws_cloudfront_distribution.backend_api.domain_name}"
}

# Output for GitHub Actions secrets
output "github_secrets" {
  description = "Values needed for GitHub Actions secrets"
  value = {
    S3_BUCKET_NAME             = aws_s3_bucket.frontend.bucket
    CLOUDFRONT_DISTRIBUTION_ID = aws_cloudfront_distribution.frontend.id
    VUE_APP_BACKEND_URL        = "https://${aws_cloudfront_distribution.backend_api.domain_name}"
    FRONTEND_URL               = "https://${aws_cloudfront_distribution.frontend.domain_name}"
  }
  sensitive = false
} 