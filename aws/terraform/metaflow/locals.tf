locals {
  resource_prefix = var.app
  resource_suffix = "${var.env}${module.common_vars.workspace_suffix}"

  metaflow_batch_image_name = "${local.resource_prefix}-batch-${local.resource_suffix}"
}
