locals {
  resource_prefix = var.app
  resource_suffix = "${var.env}${module.common_vars.workspace_suffix}-${lookup(module.common_vars.aws_regions, data.aws_region.current.name, "")}"

  aws_region     = data.aws_region.current.name
  aws_account_id = data.aws_caller_identity.current.account_id

  metaflow_config_filename = "metaflow_config_${var.env}_${data.aws_region.current.name}.json"
  metaflow_user_role_name  = "${local.resource_prefix}-metaflow_user-${local.resource_suffix}"
}
