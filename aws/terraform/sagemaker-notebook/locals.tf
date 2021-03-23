locals {
  resource_prefix = var.app
  resource_suffix = "${var.env}${module.common_vars.workspace_suffix}"

  standard_tags = module.common_vars.tags

  # Name of Sagemaker IAM role
  sagemaker_execution_role_name = "${local.resource_prefix}-sm-execution-role-${local.resource_suffix}-${var.aws_region}"
}
