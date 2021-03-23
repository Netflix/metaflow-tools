resource "aws_kms_key" "secrets-manager" {
  description = "This key is used to encrypt and decrypt the Secrets Manager secret."

  tags = module.common_vars.tags
}
