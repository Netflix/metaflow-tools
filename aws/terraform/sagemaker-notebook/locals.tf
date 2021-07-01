locals {
  resource_prefix = var.app
  resource_suffix = "${var.env}${module.common_vars.workspace_suffix}"

  aws_region     = data.aws_region.current.name
  aws_account_id = data.aws_caller_identity.current.account_id
  standard_tags  = module.common_vars.tags

  # Name of Sagemaker IAM role
  sagemaker_execution_role_name = "${local.resource_prefix}-sm-execution-role-${local.resource_suffix}-${var.aws_region}"
}
