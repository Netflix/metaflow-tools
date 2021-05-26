locals {
  resource_prefix          = var.app
  resource_suffix          = "${var.env}${module.common_vars.workspace_suffix}-${data.aws_region.current.name}"
  metaflow_config_filename = "metaflow_config_${var.env}_${data.aws_region.current.name}.json"
}
