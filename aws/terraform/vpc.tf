provider "aws" {
  region = "us-east-1"
}

# Create VPC for Batch jobs to run in
resource "aws_vpc" "metaflow" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "metaflow-vpc"
  }
}

/*
 Setup a gateway between aws VPC and internet. Allow access to and from Resources
 in subnet with public IP addr.
 Ref: https://nickcharlton.net/posts/terraform-aws-vpc.html
*/
resource "aws_internet_gateway" "metaflow" {
  vpc_id = aws_vpc.metaflow.id
}

# Create a public Subnet inside that VPC and give it a subset of VPC IP addr
resource "aws_subnet" "metaflow_batch" {
  vpc_id                  = aws_vpc.metaflow.id
  cidr_block              = "10.0.0.0/20"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1b"

  tags = {
    Name     = var.batch_subnet_name
    Metaflow = "true"
  }
}

/*
 Create public subnet and give it a subset of IP addr from our VPC disjoint
 from previous subnet.
 Ref: https://gruntwork.io/guides/networking/how-to-deploy-production-grade-vpc
 -aws/#regions_azs
*/
resource "aws_subnet" "metaflow_ecs" {
  vpc_id                  = aws_vpc.metaflow.id
  cidr_block              = "10.0.16.0/20"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a"

  tags = {
    Name     = var.ecs_subnet_name
    Metaflow = "true"
  }
}

/*
 Define a routing table for the subnets created. dest cidr_block = any IP addr
 and target = gateway_id so for any IP address route to gateway.
*/
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.metaflow.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.metaflow.id
  }

  tags = {
    Name     = "Public Subnet"
    Metaflow = "true"
  }
}

/*
 Use the routing table for batch subnet.
*/
resource "aws_route_table_association" "us_east_1a_public" {
  subnet_id      = aws_subnet.metaflow_batch.id
  route_table_id = aws_route_table.public.id
}

/*
 Use the routing table for ecs subnet.
*/
resource "aws_route_table_association" "us_east_1b_public" {
  subnet_id      = aws_subnet.metaflow_ecs.id
  route_table_id = aws_route_table.public.id
}
