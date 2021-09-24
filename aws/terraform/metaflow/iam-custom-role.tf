data "aws_iam_policy_document" "metaflow_user_role_assume_role" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    effect = "Allow"

    principals {
      identifiers = [
        module.metaflow.metadata_svc_ecs_task_role_arn
      ]
      type = "AWS"
    }
  }
}

resource "aws_iam_role" "metaflow_user_role" {
  count = var.custom_role ? 1 : 0
  name  = local.metaflow_user_role_name
  # Read more about ECS' `task_role` and `execution_role` here https://stackoverflow.com/a/49947471
  assume_role_policy = data.aws_iam_policy_document.metaflow_user_role_assume_role.json

  tags = module.common_vars.tags
}

data "aws_iam_policy_document" "metaflow_policy" {
  statement {
    effect = "Allow"

    actions = [
      "cloudformation:DescribeStacks",
      "cloudformation:*Stack",
      "cloudformation:*ChangeSet"
    ]

    resources = [
      "arn:${var.iam_partition}:cloudformation:${local.aws_region}:${local.aws_account_id}:stack/${local.resource_prefix}*${local.resource_suffix}"
    ]
  }

  statement {
    actions = [
      "s3:*Object"
    ]

    effect = "Allow"

    resources = [
      "${module.metaflow.metaflow_s3_bucket_arn}/*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "sagemaker:DescribeNotebook*",
      "sagemaker:StartNotebookInstance",
      "sagemaker:StopNotebookInstance",
      "sagemaker:UpdateNotebookInstance",
      "sagemaker:CreatePresignedNotebookInstanceUrl",
    ]

    resources = [
      "arn:${var.iam_partition}:sagemaker:${local.aws_region}:${local.aws_account_id}:notebook-instance/${local.resource_prefix}*${local.resource_suffix}",
      "arn:${var.iam_partition}:sagemaker:${local.aws_region}:${local.aws_account_id}:notebook-instance-lifecycle-config/basic*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "iam:PassRole",
    ]

    resources = [
      "arn:${var.iam_partition}:iam::${local.aws_account_id}:role/${local.resource_prefix}*${local.resource_suffix}"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey"
    ]

    resources = [
      "arn:${var.iam_partition}:kms:${local.aws_region}:${local.aws_account_id}:key/"
    ]
  }
}

data "aws_iam_policy_document" "batch_perms" {
  statement {
    sid = "JobsPermissions"

    effect = "Allow"

    actions = [
      "batch:TerminateJob",
      "batch:DescribeJobs",
      "batch:DescribeJobDefinitions",
      "batch:DescribeJobQueues",
      "batch:RegisterJobDefinition",
      "batch:DescribeComputeEnvironments",
    ]

    resources = [
      "*"
    ]
  }

  statement {
    sid = "DefinitionsPermissions"

    effect = "Allow"

    actions = [
      "batch:SubmitJob"
    ]

    resources = [
      module.metaflow.METAFLOW_BATCH_JOB_QUEUE,
      "arn:${var.iam_partition}:batch:${local.aws_region}:${local.aws_account_id}:job-definition/*:*",
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
      module.metaflow.metaflow_s3_bucket_arn
    ]
  }
}

data "aws_iam_policy_document" "log_perms" {
  statement {
    sid = "GetLogs"

    effect = "Allow"

    actions = [
      "logs:GetLogEvents"
    ]

    resources = [
      "arn:${var.iam_partition}:logs:${local.aws_region}:${local.aws_account_id}:log-group:*:log-stream:*",
    ]
  }
}

data "aws_iam_policy_document" "allow_sagemaker" {
  statement {
    sid = "AllowSagemakerCreate"

    effect = "Allow"

    actions = [
      "sagemaker:CreateTrainingJob"
    ]

    resources = [
      "arn:${var.iam_partition}:sagemaker:${local.aws_region}:${local.aws_account_id}:training-job/*",
    ]
  }

  statement {
    sid = "AllowSagemakerDescribe"

    effect = "Allow"

    actions = [
      "sagemaker:DescribeTrainingJob"
    ]

    resources = [
      "arn:${var.iam_partition}:sagemaker:${local.aws_region}:${local.aws_account_id}:training-job/*",
    ]
  }
}

data "aws_iam_policy_document" "allow_step_functions" {
  statement {
    sid = "TasksAndExecutionsGlobal"

    effect = "Allow"

    actions = [
      "states:ListStateMachines"
    ]

    resources = [
      "*",
    ]
  }

  statement {
    sid = "StateMachines"

    effect = "Allow"

    actions = [
      "states:DescribeStateMachine",
      "states:UpdateStateMachine",
      "states:StartExecution",
      "states:CreateStateMachine",
      "states:ListExecutions",
      "states:StopExecution"
    ]

    resources = [
      "arn:${var.iam_partition}:states:${local.aws_region}:${local.aws_account_id}:stateMachine:*",
    ]
  }
}

data "aws_iam_policy_document" "allow_event_bridge" {
  statement {
    sid = "RuleMaintenance"

    effect = "Allow"

    actions = [
      "events:PutTargets",
      "events:DisableRule",
    ]

    resources = [
      "arn:${var.iam_partition}:events:${local.aws_region}:${local.aws_account_id}:rule/*",
    ]
  }

  statement {
    sid = "PutRule"

    effect = "Allow"

    actions = [
      "events:PutRule",
    ]

    resources = [
      "arn:${var.iam_partition}:events:${local.aws_region}:${local.aws_account_id}:rule/*",
    ]

    condition {
      test = "Null"
      values = [
        true
      ]
      variable = "events:source"
    }
  }
}

resource "aws_iam_role_policy" "grant_metaflow_policy" {
  count  = var.custom_role ? 1 : 0
  name   = "metaflow"
  role   = aws_iam_role.metaflow_user_role[0].name
  policy = data.aws_iam_policy_document.metaflow_policy.json
}

resource "aws_iam_role_policy" "grant_batch_perms" {
  count  = var.custom_role ? 1 : 0
  name   = "batch"
  role   = aws_iam_role.metaflow_user_role[0].name
  policy = data.aws_iam_policy_document.batch_perms.json
}

resource "aws_iam_role_policy" "grant_custom_s3_list_access" {
  count  = var.custom_role ? 1 : 0
  name   = "s3_list"
  role   = aws_iam_role.metaflow_user_role[0].name
  policy = data.aws_iam_policy_document.custom_s3_list_access.json
}

resource "aws_iam_role_policy" "grant_log_perms" {
  count  = var.custom_role ? 1 : 0
  name   = "log"
  role   = aws_iam_role.metaflow_user_role[0].name
  policy = data.aws_iam_policy_document.log_perms.json
}

resource "aws_iam_role_policy" "grant_allow_sagemaker" {
  count  = var.custom_role ? 1 : 0
  name   = "sagemaker"
  role   = aws_iam_role.metaflow_user_role[0].name
  policy = data.aws_iam_policy_document.allow_sagemaker.json
}

resource "aws_iam_role_policy" "grant_allow_step_functions" {
  count  = var.custom_role ? 1 : 0
  name   = "step_functions"
  role   = aws_iam_role.metaflow_user_role[0].name
  policy = data.aws_iam_policy_document.allow_step_functions.json
}

resource "aws_iam_role_policy" "grant_allow_event_bridge" {
  count  = var.custom_role ? 1 : 0
  name   = "event_bridge"
  role   = aws_iam_role.metaflow_user_role[0].name
  policy = data.aws_iam_policy_document.allow_event_bridge.json
}
