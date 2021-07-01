resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(
    module.common_vars.tags,
    {
      Name = "${local.resource_prefix}-vpc-${local.resource_suffix}"
    }
  )
}

# Two subnets are used to leverage two separate availability zones

resource "aws_subnet" "subnet1" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.subnet1_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(
    module.common_vars.tags,
    {
      Name     = local.subnet1_name
      Metaflow = "true"
    }
  )
}

resource "aws_subnet" "subnet2" {
  availability_zone       = data.aws_availability_zones.available.names[1]
  cidr_block              = var.subnet2_cidr
  map_public_ip_on_launch = true
  vpc_id                  = aws_vpc.this.id

  tags = merge(
    module.common_vars.tags,
    {
      Name     = local.subnet2_name
      Metaflow = "true"
    }
  )
}

/*
 Setup a gateway between Amazon VPC and internet. Allow access to and from resources
 in subnet with public IP addr.
 Ref: https://nickcharlton.net/posts/terraform-aws-vpc.html
*/
resource "aws_internet_gateway" "internet_gateway" {
  vpc_id = aws_vpc.this.id

  tags = merge(
    module.common_vars.tags,
    {
      Name = "${local.resource_prefix}-internet-gateway-${local.resource_suffix}"
    }
  )
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.this.id

  tags = merge(
    module.common_vars.tags,
    {
      Name     = "Public Subnet"
      Metaflow = "true"
    }
  )
}

/*
 Map all traffic to the internet gateway for egress.
 This allows all traffic to appear to come from the associated EIP.
*/
resource "aws_route" "this" {
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.internet_gateway.id
  route_table_id         = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "subnet1_rta" {
  subnet_id      = aws_subnet.subnet1.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "subnet2_rta" {
  subnet_id      = aws_subnet.subnet2.id
  route_table_id = aws_route_table.public_route_table.id
}
