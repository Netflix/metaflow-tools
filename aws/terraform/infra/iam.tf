data "aws_iam_policy_document" "metaflow" {
  statement {
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:PutObject"
    ]

    resources = [
      aws_s3_bucket.data_sets.arn,
      "${aws_s3_bucket.data_sets.arn}/*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey"
    ]

    resources = [
      aws_kms_key.secrets-manager.arn
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = [
      aws_secretsmanager_secret.secrets.arn
    ]
  }
}

resource "aws_iam_policy" "metaflow" {
  name        = "${local.resource_prefix}-metaflow-policy-${local.resource_suffix}"
  description = "Policy to allow metaflow role to acccess s3, kms and secrets"

  policy = data.aws_iam_policy_document.metaflow.json
}
