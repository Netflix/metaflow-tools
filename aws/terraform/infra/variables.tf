variable "app" {
  type        = string
  default     = "metaflow-infra"
  description = "Name of the application"
}

variable "aws_region" {
  type        = string
  default     = "us-west-2"
  description = "AWS region we will deploy to."
}

variable "env" {
  type        = string
  default     = "dev"
  description = "The environment for this stack to be created in. Used for the tfstate bucket and naming scope of resources."
}

variable "subnet1_cidr" {
  type        = string
  default     = "10.20.0.0/24"
  description = "CIDR for Metaflow VPC Subnet 1"
}

variable "subnet2_cidr" {
  type        = string
  default     = "10.20.1.0/24"
  description = "CIDR for Metaflow VPC Subnet 1"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.20.0.0/16"
  description = "CIDR for the Metaflow VPC"
}
