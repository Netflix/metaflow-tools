resource "aws_s3_bucket" "data_sets" {
  bucket = ${local.resource_prefix}-${var.base_s3_data_sets_bucket_name}-${local.resource_suffix}
  acl    = "private"

  tags = module.common_vars.tags
}
