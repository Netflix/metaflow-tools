variable "app" {
  default     = "metaflow"
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

variable "enable_step_functions" {
  type        = bool
  description = "Provisions infrastructure for step functions if enabled"
}

variable "access_list_cidr_blocks" {
  type        = list(string)
  description = "List of CIDRs we want to grant access to our Metaflow Metadata Service. Usually this is your VPN's CIDR blocks."
  default     = []
}

variable "cpu_max_compute_vcpus" {
  type        = string
  description = "Maximum number of EC2 vCPUs that our CPU Batch Compute Environment can reach."
  default     = 64
}

variable "cpu_min_compute_vcpus" {
  type        = string
  description = "Minimum number of EC2 vCPUs that our CPU Batch Compute Environment should maintain."
  default     = 16
}

variable "cpu_desired_compute_vcpus" {
  type        = string
  description = "Desired number of EC2 vCPUS in our CPU Batch Compute Environment. A non-zero number will ensure instances are always on and avoid some cold-start problems."
  default     = 16
}

variable "large_cpu_max_compute_vcpus" {
  type        = string
  description = "Maximum number of EC2 vCPUs that our large CPU Batch Compute Environment can reach."
  default     = 128
}

variable "large_cpu_min_compute_vcpus" {
  type        = string
  description = "Minimum number of EC2 vCPUs that our large CPU Batch Compute Environment should maintain."
  default     = 0
}

variable "large_cpu_desired_compute_vcpus" {
  type        = string
  description = "Desired number of EC2 vCPUS in our large CPU Batch Compute Environment. A non-zero number will ensure instances are always on and avoid some cold-start problems."
  default     = 0
}

variable "gpu_max_compute_vcpus" {
  type        = string
  description = "Maximum number of EC2 vCPUs that our GPU Batch Compute Environment can reach."
  default     = 64
}

variable "gpu_min_compute_vcpus" {
  type        = string
  description = "Minimum number of EC2 vCPUs that our GPU Batch Compute Environment should maintain."
  default     = 0
}

variable "gpu_desired_compute_vcpus" {
  type        = string
  description = "Desired number of EC2 vCPUS in our GPU Batch Compute Environment. A non-zero number will ensure instances are always on and avoid some cold-start problems."
  default     = 0
}
