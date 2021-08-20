module "common_vars" {
  source = "../modules/common"

  app = var.app
  env = var.env
}
