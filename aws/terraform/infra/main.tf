provider "aws" {
  region = var.aws_region
}

module "common_vars" {
  source = "../common"

  app = var.app
  env = var.env
}
