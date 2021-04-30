output "METAFLOW_DATASTORE_SYSROOT_S3" {
  value       = module.metaflow.METAFLOW_DATASTORE_SYSROOT_S3
  description = "Amazon S3 URL for Metaflow DataStore"
}

output "METAFLOW_DATATOOLS_S3ROOT" {
  value       = module.metaflow.METAFLOW_DATATOOLS_S3ROOT
  description = "Amazon S3 URL for Metaflow DataTools"
}

output "METAFLOW_BATCH_JOB_QUEUE" {
  value       = module.metaflow.METAFLOW_BATCH_JOB_QUEUE
  description = "AWS Batch Job Queue ARN for Metaflow"
}

output "METAFLOW_ECS_S3_ACCESS_IAM_ROLE" {
  value       = module.metaflow.METAFLOW_ECS_S3_ACCESS_IAM_ROLE
  description = "Role for AWS Batch to Access Amazon S3 ARN"
}

output "METAFLOW_SERVICE_URL" {
  value       = module.metaflow.METAFLOW_SERVICE_URL
  description = "URL for Metadata Service (Accessible in VPC)"
}

output "METAFLOW_SERVICE_INTERNAL_URL" {
  value       = module.metaflow.METAFLOW_SERVICE_INTERNAL_URL
  description = "URL for Metadata Service (Accessible in VPC)"
}

output "METAFLOW_SFN_IAM_ROLE" {
  value       = module.metaflow.METAFLOW_SFN_IAM_ROLE
  description = "IAM role for AWS Step Functions to access AWS resources (AWS Batch, AWS DynamoDB)."
}

output "METAFLOW_EVENTS_SFN_ACCESS_IAM_ROLE" {
  value       = module.metaflow.METAFLOW_EVENTS_SFN_ACCESS_IAM_ROLE
  description = "IAM role for Amazon EventBridge to access AWS Step Functions."
}

output "METAFLOW_SFN_DYNAMO_DB_TABLE" {
  value       = module.metaflow.METAFLOW_SFN_DYNAMO_DB_TABLE
  description = "AWS DynamoDB table name for tracking AWS Step Functions execution metadata."
}

output "metaflow_profile_json" {
  value       = module.metaflow.metaflow_profile_json
  description = "Metaflow profile JSON object that can be used to communicate with this Metaflow Stack. Store this in `~/.metaflow/config_[stack-name]` and select with `$ export METAFLOW_PROFILE=[stack-name]`."
}

# output for sagemaker notebook project

output "metaflow_s3_bucket_name" {
  value       = module.metaflow.metaflow_s3_bucket_name
  description = "The name of the bucket we'll be using as blob storage"
}

output "metaflow_s3_bucket_arn" {
  value       = module.metaflow.metaflow_s3_bucket_arn
  description = "The ARN of the bucket we'll be using as blob storage"
}

output "metaflow_s3_bucket_policy" {
  value       = module.metaflow.metaflow_s3_bucket_policy
  description = "Policy grants access to the Metaflow S3 bucket used for blob storage by the Datastore"
}

output "metaflow_s3_bucket_kms_key_policy" {
  value       = module.metaflow.metaflow_s3_bucket_kms_key_policy
  description = "The ARN of the KMS key used to encrypt the Metaflow datastore S3 bucket"
}

output "metaflow_api_gateway_rest_api_id" {
  value       = module.metaflow.metaflow_api_gateway_rest_api_id
  description = "The ID of the API Gateway REST API we'll use to accept MetaData service requests to forward to the Fargate API instance"
}

output "metaflow_batch_container_image" {
  value       = module.metaflow.metaflow_batch_container_image
  description = "The ECR repo containing the metaflow batch image"
}
