#!/bin/bash
# userdata.sh — runs once on EC2 first boot
# Installs Docker, AWS CLI, configures ECR credential helper
set -euo pipefail

LOG=/var/log/userdata.log
exec > >(tee -a $LOG) 2>&1

echo "=== Bootstrap started at $(date) ==="

# Update system
dnf update -y

# Install Docker
dnf install -y docker
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

# Install AWS CLI v2 (already included in Amazon Linux 2023)
# Verify it's available
aws --version

# Install Amazon ECR credential helper
# This lets Docker authenticate with ECR automatically using the instance role
dnf install -y amazon-ecr-credential-helper

# Configure Docker to use ECR credential helper
mkdir -p /root/.docker
cat > /root/.docker/config.json <<'EOF'
{
  "credHelpers": {
    "${ecr_registry}": "ecr-login"
  }
}
EOF

# Also configure for ec2-user
mkdir -p /home/ec2-user/.docker
cat > /home/ec2-user/.docker/config.json <<EOF
{
  "credHelpers": {
    "${ecr_registry}": "ecr-login"
  }
}
EOF
chown -R ec2-user:ec2-user /home/ec2-user/.docker

# Install useful tools
dnf install -y htop wget curl git

# Configure AWS region for CLI
mkdir -p /home/ec2-user/.aws
cat > /home/ec2-user/.aws/config <<EOF
[default]
region = ${aws_region}
output = json
EOF
chown -R ec2-user:ec2-user /home/ec2-user/.aws

# Create app directory
mkdir -p /opt/${app_name}
chown ec2-user:ec2-user /opt/${app_name}

# Open firewall for app port (security group handles external, this is local)
echo "App will listen on port ${app_port}"

# Signal completion
echo "=== Bootstrap COMPLETE at $(date) ==="
echo "Docker version: $(docker --version)"
echo "AWS CLI version: $(aws --version)"
echo "Ready for deployments via GitHub Actions!"
