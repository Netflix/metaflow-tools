provider "aws" {
  region = var.aws_region
}

data "terraform_remote_state" "infra" {
  backend = "local"

  config = {
    path = "../infra/terraform.tfstate"
  }
}

data "aws_region" "current" {}

module "common_vars" {
  source = "../modules/common"

  app = var.app
  env = var.env
}

module "metaflow" {
  source = "../modules/metaflow"

  resource_prefix = local.resource_prefix
  resource_suffix = local.resource_suffix

  enable_step_functions = var.enable_step_functions
  metaflow_policy_arn   = data.terraform_remote_state.infra.outputs.metaflow_policy_arn
  tags                  = module.common_vars.tags

  cpu_max_compute_vcpus           = var.cpu_max_compute_vcpus
  cpu_desired_compute_vcpus       = var.cpu_desired_compute_vcpus
  cpu_min_compute_vcpus           = var.cpu_min_compute_vcpus
  large_cpu_max_compute_vcpus     = var.large_cpu_max_compute_vcpus
  large_cpu_desired_compute_vcpus = var.large_cpu_desired_compute_vcpus
  large_cpu_min_compute_vcpus     = var.large_cpu_min_compute_vcpus
  gpu_max_compute_vcpus           = var.gpu_max_compute_vcpus
  gpu_desired_compute_vcpus       = var.gpu_desired_compute_vcpus
  gpu_min_compute_vcpus           = var.gpu_min_compute_vcpus

  access_list_cidr_blocks = var.access_list_cidr_blocks
  vpc_id                  = data.terraform_remote_state.infra.outputs.vpc_id
  vpc_cidr_block          = data.terraform_remote_state.infra.outputs.vpc_cidr_block
  subnet_private_1_id     = data.terraform_remote_state.infra.outputs.subnet_private_1_id
  subnet_private_2_id     = data.terraform_remote_state.infra.outputs.subnet_private_2_id
}
