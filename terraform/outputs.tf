################################################################################
# outputs.tf
################################################################################

output "ec2_public_ip" {
  description = "Static public IP of your EC2 instance (add to EC2_HOST secret)"
  value       = aws_eip.app.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "ecr_repository_url" {
  description = "Full ECR repository URL (use in workflow as image prefix)"
  value       = aws_ecr_repository.app.repository_url
}

output "ssh_command" {
  description = "SSH command to connect to your server"
  value       = "ssh -i cicd-demo-key ec2-user@${aws_eip.app.public_ip}"
}

output "app_url" {
  description = "Application URL once deployed"
  value       = "http://${aws_eip.app.public_ip}:3000"
}

output "health_url" {
  description = "Health check endpoint"
  value       = "http://${aws_eip.app.public_ip}:3000/health"
}

output "next_steps" {
  description = "What to do after terraform apply"
  value       = <<-EOT
    ✅ Infrastructure ready! Now:
    1. Copy EC2 public IP to GitHub Secret: EC2_HOST = ${aws_eip.app.public_ip}
    2. Wait ~2 minutes for EC2 user_data to finish (Docker install)
    3. SSH in to verify: ssh -i cicd-demo-key ec2-user@${aws_eip.app.public_ip}
    4. Check Docker is running: docker --version
    5. Push to main branch to trigger first deployment
  EOT
}

output "free_tier_summary" {
  description = "Cost breakdown"
  value       = <<-EOT
    MONTHLY COST ESTIMATE:
    ─────────────────────────────────────────
    EC2 t2.micro (750 hrs/mo free)  : $0.00
    ECR storage  (500 MB free)      : $0.00
    Elastic IP   (attached+running) : $0.00
    Data transfer (within region)   : $0.00
    Security groups / IAM           : $0.00
    ─────────────────────────────────────────
    TOTAL (first 12 months)         : $0.00
    ─────────────────────────────────────────
    After 12 months: ~$8.50/month
  EOT
}
