provider "aws" {
  region = var.aws_region
}

data "terraform_remote_state" "infra" {
  backend = "local"

  config = {
    path = "../infra/terraform.tfstate"
  }
}

module "common_vars" {
  source = "../common"

  app = var.app
  env = var.env
}

module "metaflow-datastore" {
  source = "./modules/datastore"

  resource_prefix                    = local.resource_prefix
  resource_suffix                    = local.resource_suffix
  metaflow_vpc_id                    = data.terraform_remote_state.infra.outputs.vpc_id
  ecs_instance_role_arn              = module.metaflow-computation.ecs_instance_role_arn
  ecs_execution_role_arn             = module.metaflow-computation.ecs_execution_role_arn
  aws_batch_service_role_arn         = module.metaflow-computation.batch_service_role_arn
  subnet_private_1_id                = data.terraform_remote_state.infra.outputs.subnet_private_1_id
  subnet_private_2_id                = data.terraform_remote_state.infra.outputs.subnet_private_2_id
  metadata_service_security_group_id = module.metaflow-metadata-service.metadata_service_security_group_id

  standard_tags = module.common_vars.tags
}

module "metaflow-metadata-service" {
  source = "./modules/metadata-service"

  resource_prefix              = local.resource_prefix
  resource_suffix              = local.resource_suffix
  metaflow_vpc_id              = data.terraform_remote_state.infra.outputs.vpc_id
  vpc_cidr_block               = data.terraform_remote_state.infra.outputs.vpc_cidr_block
  subnet_private_1_id          = data.terraform_remote_state.infra.outputs.subnet_private_1_id
  subnet_private_2_id          = data.terraform_remote_state.infra.outputs.subnet_private_2_id
  rds_master_instance_endpoint = module.metaflow-datastore.rds_master_instance_endpoint
  database_username            = module.metaflow-datastore.database_username
  database_password            = module.metaflow-datastore.database_password
  fargate_task_role_arn        = module.metaflow-datastore.iam_s3_access_role_arn
  fargate_execution_role_arn   = module.metaflow-computation.ecs_execution_role_arn
  access_list_cidr_blocks      = var.access_list_cidr_blocks

  standard_tags = module.common_vars.tags
}

module "metaflow-computation" {
  source = "./modules/computation"

  resource_prefix                                   = local.resource_prefix
  resource_suffix                                   = local.resource_suffix
  metaflow_vpc_id                                   = data.terraform_remote_state.infra.outputs.vpc_id
  subnet_private_1_id                               = data.terraform_remote_state.infra.outputs.subnet_private_1_id
  subnet_private_2_id                               = data.terraform_remote_state.infra.outputs.subnet_private_2_id
  s3_kms_policy_arn                                 = module.metaflow-datastore.metaflow_kms_s3_policy_arn
  metaflow_policy_arn                               = data.terraform_remote_state.infra.outputs.metaflow_policy_arn
  batch_compute_environment_cpu_max_vcpus           = var.cpu_max_compute_vcpus
  batch_compute_environment_cpu_desired_vcpus       = var.cpu_desired_compute_vcpus
  batch_compute_environment_cpu_min_vcpus           = var.cpu_min_compute_vcpus
  batch_compute_environment_large_cpu_max_vcpus     = var.large_cpu_max_compute_vcpus
  batch_compute_environment_large_cpu_desired_vcpus = var.large_cpu_desired_compute_vcpus
  batch_compute_environment_large_cpu_min_vcpus     = var.large_cpu_min_compute_vcpus
  batch_compute_environment_gpu_max_vcpus           = var.gpu_max_compute_vcpus
  batch_compute_environment_gpu_desired_vcpus       = var.gpu_desired_compute_vcpus
  batch_compute_environment_gpu_min_vcpus           = var.gpu_min_compute_vcpus

  standard_tags = module.common_vars.tags
}

module "metaflow-step-functions" {
  source = "./modules/step-functions"

  active          = var.enable_step_functions
  resource_prefix = local.resource_prefix
  resource_suffix = local.resource_suffix

  batch_job_queue_arn = module.metaflow-computation.METAFLOW_BATCH_JOB_QUEUE
  s3_bucket_arn       = module.metaflow-datastore.s3_bucket_arn
  s3_bucket_kms_arn   = module.metaflow-datastore.datastore_s3_bucket_kms_key_arn

  standard_tags = module.common_vars.tags
}
