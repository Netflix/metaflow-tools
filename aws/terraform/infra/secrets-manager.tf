resource aws_secretsmanager_secret "secrets" {
  name        = "${local.resource_prefix}-${local.resource_suffix}"
  description = "Secret for securely storing credentials"

  kms_key_id = aws_kms_key.secrets-manager.id

  tags = module.common_vars.tags
}
