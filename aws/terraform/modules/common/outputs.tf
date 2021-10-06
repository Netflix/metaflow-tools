output "app" {
  value = var.app
}

output "env" {
  value = var.env
}

output "tags" {
  value = merge(
    var.tags,
    {
      "application"  = var.app,
      "environment"  = var.env,
      "tf.workspace" = terraform.workspace
    }
  )
}

output "workspace_suffix" {
  value = terraform.workspace == "default" ? "" : "-${terraform.workspace}"
}

output "aws_regions" {
  value = local.aws_regions
}
