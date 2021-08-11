output "subnet1_id" {
  value       = aws_subnet.subnet1.id
  description = "First subnet used for availability zone redundancy"
}

output "subnet2_id" {
  value       = aws_subnet.subnet2.id
  description = "Second subnet used for availability zone redundancy"
}

output "vpc_cidr_block" {
  value       = aws_vpc.this.cidr_block
  description = "The CIDR block we've designated for this VPC"
}

output "vpc_id" {
  value       = aws_vpc.this.id
  description = "The id of the single VPC we stood up for all Metaflow resources to exist in."
}
