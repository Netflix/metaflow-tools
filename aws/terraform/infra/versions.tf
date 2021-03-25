terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.16.0"
    }
  }
  required_version = ">= 0.13"
}
