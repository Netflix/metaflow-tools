resource "aws_vpc" "this" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = merge(
    module.common_vars.tags,
    {
      Name = "${local.resource_prefix}-vpc-${local.resource_suffix}"
    }
  )
}

/*
 Setup a gateway between aws VPC and internet. Allow access to and from Resources
 in subnet with public IP addr.
 Ref: https://nickcharlton.net/posts/terraform-aws-vpc.html
*/
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(
    module.common_vars.tags,
    {
      Name = "${local.resource_prefix}-internet-gateway-${local.resource_suffix}"
    }
  )
}

/*
 Create a public Subnet that the two follow private Subnets can use for internet egress connections.
 Contains our NAT Gateway.
*/
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.0.32.0/20"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = merge(
    module.common_vars.tags,
    {
      Name = local.public_subnet_name
    }
  )
}

resource "aws_eip" "vpc_egress" {
  vpc              = true
  public_ipv4_pool = "amazon"
}

# Create the NAT Gateway that will be used by the private Subnets
resource "aws_nat_gateway" "metaflow_nat_gateway" {
  allocation_id = aws_eip.vpc_egress.id
  subnet_id     = aws_subnet.public.id

  depends_on = [aws_internet_gateway.this]

  tags = merge(
    module.common_vars.tags,
    {
      Name = "${local.resource_prefix}-nat-${local.resource_suffix}"
    }
  )
}

# Two private subnets are used to leverage two separate availability zones

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = "10.0.0.0/20"
  availability_zone = "${var.aws_region}b"

  tags = merge(
    module.common_vars.tags,
    {
      Name     = local.subnet_private_1_name
      Metaflow = "true"
    }
  )
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = "10.0.16.0/20"
  availability_zone = "${var.aws_region}a"

  tags = merge(
    module.common_vars.tags,
    {
      Name     = local.subnet_private_2_name
      Metaflow = "true"
    }
  )
}

resource "aws_route_table" "public" {
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
 Maps all traffic to the internet gateway for egress.
 This allows all traffic to appear to come from the associated EIP.
*/
resource "aws_route" "this" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.metaflow_nat_gateway.id
  }

  tags = module.common_vars.tags
}

resource "aws_route_table_association" "public_subnet_route_table_association" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private.id
}

resource "aws_flow_log" "main_vpc" {
  count                = length(var.vpc_flow_log_s3_destination) > 0 ? 1 : 0
  vpc_id               = aws_vpc.this.id
  traffic_type         = "ALL"
  log_destination_type = "s3"
  log_destination      = var.vpc_flow_log_s3_destination
  tags                 = module.common_vars.tags
}
