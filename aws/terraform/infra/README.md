# Infra

Stands up the base infrastructure required to deploy a Metaflow stack.

Mostly stands up and configures the VPC.

## AWS Resources

### VPC

Virtual Private Cloud with two private subnets in different availability zones and a public subnet. Also includes an Elastic IP address for VPC egress (`elastic_ip_allocation_id`) to allow external services to whitelist access by ip.

### S3 Bucket

S3 bucket for flow data input / output.

### Secret

Secretsmanager Secret for storing secrets used in flows.

### IAM Policy

IAM policy to allow access to the above S3 bucekt and secret.
