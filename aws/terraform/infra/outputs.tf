output "vpc_id" {
  value       = aws_vpc.this.id
  description = "The id of the single VPC we stood up for all Metaflow resources to exist in."
}

output "subnet_private_1_id" {
  value       = aws_subnet.private_1.id
  description = "First private subnet used for availability zone redundancy"
}

output "subnet_private_2_id" {
  value       = aws_subnet.private_2.id
  description = "Second private subnet used for availability zone redundancy"
}

output "vpc_cidr_block" {
  value       = aws_vpc.this.cidr_block
  description = "The CIDR block we've designated for this VPC"
}

output "metaflow_policy_arn" {
  value       = aws_iam_policy.metaflow.arn
  description = "The ARN of the policy that allows to Metaflow S3 buckets, KMS keys, and secrets"
}

output "elastic_ip_allocation_id" {
  value       = aws_eip.vpc_egress.id
  description = "Elastic IP allocation ID used to ensure egress traffic has a static IP."
}
