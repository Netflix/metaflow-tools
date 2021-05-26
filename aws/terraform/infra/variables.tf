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

variable "vpc_cidr" {
  type        = string
  default     = "10.0.32.0/20"
  description = "Amazon VPC cidr block"
}

variable "subnet1_cidr" {
  type        = string
  default     = "10.0.0.0/20"
  description = "Private subnet1 cidr block"
}

variable "subnet2_cidr" {
  type        = string
  default     = "10.0.16.0/20"
  description = "Private subnet1 cidr block"
}
