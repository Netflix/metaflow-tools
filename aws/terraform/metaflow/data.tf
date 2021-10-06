data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "terraform_remote_state" "infra" {
  backend = "local"

  config = {
    path = "../infra/terraform.tfstate"
  }
}
