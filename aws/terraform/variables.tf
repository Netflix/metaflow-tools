variable "bucket_name" {
  type        = string
  description = "name of S3 bucket to persist metaflow data in; defaults to 'metaflow'"
  default     = "metaflow"
}

variable "compute_env_name" {
  type        = string
  description = "name of Batch compute environment; defaults to 'metaflow'"
  default     = "metaflow"
}

variable "ecs_instance_role_name" {
  type        = string
  description = "name of ECS IAM instance role; defaults to 'ecs_instance_role'"
  default     = "ecs_instance_role"
}

variable "batch_service_role_name" {
  type        = string
  description = "name of Batch service IAM role; defaults to 'aws_batch_service_role'"
  default     = "aws_batch_service_role"
}

variable "batch_security_group_name" {
  type        = string
  description = "name of Batch service's security group used on the compute environment; defaults to 'aws_batch_compute_environment_security_group'"
  default     = "aws_batch_compute_environment_security_group"
}

variable "service_security_group_name" {
  type        = string
  description = "name of ECS service's security group used on the metaflow service; defaults to 'aws_ecs_metaflow_security_group'"
  default     = "aws_ecs_metaflow_security_group"
}

variable "db_security_group_name" {
  type        = string
  description = "name of PostgresQL database's security group; defaults to 'metaflow_postgresql'"
  default     = "metaflow_postgresql"
}



variable "batch_instance_type" {
  type        = string
  description = "EC2 instance type to use for Batch jobs; defaults to 'c4.large'"
  default     = "c4.large"
}

variable "batch_max_cpu" {
  type        = string
  description = "maximum number of vCPUs to use on a batch job; defaults to 32"
  default     = 32
}

variable "batch_min_cpu" {
  type        = string
  description = "minimum number of vCPUs to use on a batch job; defaults to 2"
  default     = 2
}

variable "batch_queue_name" {
  type        = string
  description = "name of Batch queue; defaults to 'metaflow'"
  default     = "metaflow"
}

variable "batch_subnet_name" {
  type        = string
  description = "name tag of Batch compute subnet; defaults to 'metaflow-public-1'"
  default     = "metaflow-public-1"
}


variable "ecs_subnet_name" {
  type        = string
  description = "name tag of ECS metaflow service subnet; defaults to 'metaflow-public-2'"
  default     = "metaflow-default-2"
}

variable "db_username" {
  type        = string
  description = "PostgresQL username; defaults to 'metaflow'"
  default     = "metaflow"
}

variable "db_password" {
  type        = string
  description = "PostgresSQL password; defaults to 'metaflow'"
  default     = "metaflow"
}

variable "db_name" {
  type        = string
  description = "name of PostgresQL database for metaflow service; defaults to 'metaflow'"
  default     = "metaflow"
}

variable "db_instance_type" {
  type        = string
  description = "RDS instance type to launch for PostgresQL database; defaults to 'db.t2.micro'"
  default     = "db.t2.micro"
}

variable "pg_subnet_group_name" {
  type        = string
  description = "name of PostgresQL subnet group; defaults to 'metaflow-main'"
  default     = "metaflow-main"
}

variable "ecs_cluster_name" {
  type        = string
  description = "name of metaflow ECS cluster; defaults to 'metaflow'"
  default     = "metaflow"
}

variable "my_cidr_block" {
  type        = string
  description = "your CIDR block range to allow connections to the ECS service for; defaults to '0.0.0.0/0' but note this is a security vulnerability"
  default     = "0.0.0.0/0"
}

variable "aws_profile" {
  type        = string
  description = "AWS profile to use with this terraform config; defaults to 'default'"
  default     = "default"
}

variable "aws_region" {
  type        = string
  description = "AWS region to deploy to; defaults to 'us-east-1'"
  default     = "us-east-1"
}
