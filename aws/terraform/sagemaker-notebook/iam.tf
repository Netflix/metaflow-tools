data "aws_iam_policy_document" "sagemaker_execution_role_assume_role" {
  statement {
    effect = "Allow"

    principals {
      identifiers = [
        "sagemaker.amazonaws.com"
      ]
      type = "Service"
    }

    actions = [
      "sts:AssumeRole"
    ]
  }
}

resource "aws_iam_role" "sagemaker_execution_role" {
  name        = local.sagemaker_execution_role_name
  description = "The role that our SageMaker instances uses"

  assume_role_policy = data.aws_iam_policy_document.sagemaker_execution_role_assume_role.json

  tags = local.standard_tags
}

data "aws_iam_policy_document" "iam_pass_role" {
  statement {
    sid = "AllowPassRole"

    actions = [
      "iam:PassRole"
    ]

    resources = [
      "*"
    ]

    condition {
      test = "StringEquals"
      values = [
        "sagemaker.amazonaws.com"
      ]
      variable = "iam:PassedToService"
    }
  }
}

data "aws_iam_policy_document" "misc_permissions" {
  statement {
    sid = "MiscPermissions"

    effect = "Allow"

    actions = [
      "cloudwatch:PutMetricData",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability"
    ]

    resources = [
      "*"
    ]
  }
}

data "aws_iam_policy_document" "logs_roles_policy" {
  statement {
    sid = "CreateLogStream"

    effect = "Allow"

    actions = [
      "logs:CreateLogStream"
    ]

    resources = [
      "arn:${var.iam_partition}:logs:${local.aws_region}:${local.aws_account_id}:log-group:/aws/batch/job:log-stream:*",
      "arn:${var.iam_partition}:logs:${local.aws_region}:${local.aws_account_id}:log-group:/aws/sagemaker/NotebookInstances:log-stream:*",
    ]
  }

  statement {
    sid = "LogEvents"

    effect = "Allow"

    actions = [
      "logs:PutLogEvents",
      "logs:GetLogEvents",
    ]

    resources = [
      "${aws_sagemaker_notebook_instance.this.arn}/jupyter.log",
      "${aws_sagemaker_notebook_instance.this.arn}/LifecycleConfigOnCreate",
      "arn:${var.iam_partition}:logs:${local.aws_region}:${local.aws_account_id}:log-group:/aws/batch/job:log-stream:job-queue-",
    ]
  }

  statement {
    sid = "LogGroup"

    effect = "Allow"

    actions = [
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:CreateLogGroup",
    ]

    resources = [
      "*"
    ]
  }
}

data "aws_iam_policy_document" "sagemaker_permissions" {
  statement {
    sid = "SageMakerNotebook"

    effect = "Allow"

    actions = [
      "sagemaker:DescribeNotebook*",
      "sagemaker:StartNotebookInstance",
      "sagemaker:StopNotebookInstance",
      "sagemaker:UpdateNotebookInstance",
      "sagemaker:CreatePresignedNotebookInstanceUrl"
    ]

    resources = [
      aws_sagemaker_notebook_instance.this.arn,
      "arn:${var.iam_partition}:logs:${local.aws_region}:${local.aws_account_id}:notebook-instance-lifecycle-config/basic*",
    ]
  }
}

data "aws_iam_policy_document" "custom_s3_list_access" {
  statement {
    sid = "BucketAccess"

    effect = "Allow"

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      data.terraform_remote_state.metaflow.outputs.metaflow_s3_bucket_arn
    ]
  }
}

data "aws_iam_policy_document" "custom_s3_access" {
  statement {
    sid = "ObjectAccess"

    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject"
    ]

    resources = [
      "${data.terraform_remote_state.metaflow.outputs.metaflow_s3_bucket_arn}/*"
    ]
  }
}

data "aws_iam_policy_document" "deny_presigned" {
  statement {
    sid = "DenyPresigned"

    effect = "Deny"

    actions = [
      "s3:*"
    ]

    resources = [
      "*"
    ]

    condition {
      test = "StringNotEquals"
      values = [
        "REST-HEADER"
      ]
      variable = "s3:authType"
    }
  }
}

data "aws_iam_policy_document" "s3_kms" {
  statement {
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey"
    ]

    resources = [
      data.terraform_remote_state.metaflow.outputs.datastore_s3_bucket_kms_key_arn
    ]
  }
}

resource "aws_iam_role_policy" "grant_iam_pass_role" {
  name   = "iam_pass_role"
  role   = aws_iam_role.sagemaker_execution_role.name
  policy = data.aws_iam_policy_document.iam_pass_role.json
}

resource "aws_iam_role_policy" "grant_misc_permissions_role" {
  name   = "misc_permissions"
  role   = aws_iam_role.sagemaker_execution_role.name
  policy = data.aws_iam_policy_document.misc_permissions.json
}

resource "aws_iam_role_policy" "grant_logs_roles_policy" {
  name   = "logs"
  role   = aws_iam_role.sagemaker_execution_role.name
  policy = data.aws_iam_policy_document.logs_roles_policy.json
}

resource "aws_iam_role_policy" "grant_sagemaker_permissions" {
  name   = "sagemaker"
  role   = aws_iam_role.sagemaker_execution_role.name
  policy = data.aws_iam_policy_document.sagemaker_permissions.json
}

resource "aws_iam_role_policy" "grant_custom_s3_list_access" {
  name   = "s3_list"
  role   = aws_iam_role.sagemaker_execution_role.name
  policy = data.aws_iam_policy_document.custom_s3_list_access.json
}

resource "aws_iam_role_policy" "grant_custom_s3_access" {
  name   = "s3"
  role   = aws_iam_role.sagemaker_execution_role.name
  policy = data.aws_iam_policy_document.custom_s3_access.json
}

resource "aws_iam_role_policy" "grant_deny_presigned" {
  name   = "deny_presigned"
  role   = aws_iam_role.sagemaker_execution_role.name
  policy = data.aws_iam_policy_document.deny_presigned.json
}

resource "aws_iam_role_policy" "grant_s3_kms" {
  name   = "s3_kms"
  role   = aws_iam_role.sagemaker_execution_role.name
  policy = data.aws_iam_policy_document.s3_kms.json
}
