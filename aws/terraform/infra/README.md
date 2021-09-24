# Infra

Stands up the base infrastructure required to deploy a Metaflow stack.

Mostly stands up and configures the Amazon VPC.

## AWS Resources

### Amazon VPC

Amazon Virtual Private Cloud with two private subnets in different availability zones and a public subnet. Also includes an
Elastic IP address for Amazon VPC egress (`elastic_ip_allocation_id`) to allow external services to whitelist access by IP.
