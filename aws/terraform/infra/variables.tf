variable "app" {
  type        = string
  default     = "metaflow-infra"
  description = "Name of the application"
}

variable "env" {
  type        = string
  default     = "dev"
  description = "The environment for this stack to be created in. Used for the tfstate bucket and naming scope of resources."
}

variable "aws_region" {
  type        = string
  description = "AWS region we will deploy to."
}

variable "base_s3_data_sets_bucket_name" {
  type        = string
  description = "Base name of S3 bucket to create to store external datasets/artifacts."
}

variable "vpc_flow_log_s3_destination" {
  type        = string
  description = "The ARN of the S3 bucket to receive VPC flow logs."
  default     = ""
}
