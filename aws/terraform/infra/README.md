# Infra

Stands up the base infrastructure required to deploy a Metaflow stack.

Mostly stands up and configures the VPC.

## AWS Resources

### IAM

IAM policy to allow access to the above S3 bucket and secret.

### KMS

KMS Key to encrypt/decrypt AWS Secrets Manager Secret.

### S3

S3 bucket for flow data input / output. This is not the Metaflow controlled S3 bucket but rather an external bucket 
that Metaflow users can use to transfer artifacts into and out of Metaflow.

### Secrets Manager

Secrets Manager Secret for storing secrets used in flows.

### VPC

Virtual Private Cloud with two private subnets in different availability zones and a public subnet. Also includes an 
Elastic IP address for VPC egress (`elastic_ip_allocation_id`) to allow external services to whitelist access by ip.