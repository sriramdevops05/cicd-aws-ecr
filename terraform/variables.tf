################################################################################
# variables.tf
################################################################################

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Must be staging or production."
  }
}

variable "app_name" {
  description = "Application name — used as prefix for all resource names"
  type        = string
  default     = "cicd-demo"
}

variable "ecr_repository_name" {
  description = "ECR repository name — must match ECR_REPOSITORY in workflow"
  type        = string
  default     = "my-app"
}

variable "app_port" {
  description = "Port the Docker container listens on"
  type        = number
  default     = 3000
}

variable "public_key" {
  description = "SSH public key content (paste output of: cat ~/.ssh/cicd-key.pub)"
  type        = string
  sensitive   = false
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH. Use your IP: curl ifconfig.me then append /32"
  type        = string
  default     = "0.0.0.0/0"
  validation {
    condition     = can(cidrhost(var.ssh_allowed_cidr, 0))
    error_message = "Must be a valid CIDR block, e.g. 203.0.113.42/32"
  }
}
