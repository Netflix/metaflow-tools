locals {
  resource_prefix = var.app
  resource_suffix = "${var.env}${module.common_vars.workspace_suffix}-${data.aws_region.current.name}"
}
