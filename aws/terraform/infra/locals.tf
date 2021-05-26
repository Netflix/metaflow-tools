locals {
  resource_prefix = var.app
  resource_suffix = "${var.env}${module.common_vars.workspace_suffix}"

  # Name of public AWS subnet used for egress traffic.
  public_subnet_name = "${local.resource_prefix}-public-subnet-${local.resource_suffix}"

  # Name of first private subnet.
  subnet_private_1_name = "${local.resource_prefix}-batch-subnet-${local.resource_suffix}"

  # Name of second private subnet.
  subnet_private_2_name = "${local.resource_prefix}-ecs-subnet-${local.resource_suffix}"
}
