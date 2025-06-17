# Variables for MicrohapDB Frontend Infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "haplosearch"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Custom domain name for the frontend (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain (optional)"
  type        = string
  default     = ""
}

variable "backend_url" {
  description = "Backend API URL for CORS configuration"
  type        = string
  default     = "http://54.196.254.13"
}

variable "backend_domain" {
  description = "Backend domain for CloudFront origin"
  type        = string
  default     = "ec2-54-196-254-13.compute-1.amazonaws.com"
}

# Tags to apply to all resources
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project    = "MicrohapDB"
    ManagedBy  = "Terraform"
    Repository = "https://github.com/tylerslonecki/microhapDB"
  }
} 