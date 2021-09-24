locals {
  resource_prefix = var.app
  resource_suffix = "${var.env}${module.common_vars.workspace_suffix}"

  subnet1_name = "${local.resource_prefix}-subnet-1-${local.resource_suffix}"
  subnet2_name = "${local.resource_prefix}-subnet-2-${local.resource_suffix}"
}
