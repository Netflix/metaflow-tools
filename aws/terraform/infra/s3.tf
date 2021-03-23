resource "aws_s3_bucket" "data_sets" {
  bucket = local.datasets_s3_bucket_name
  acl    = "private"

  tags = module.common_vars.tags
}
