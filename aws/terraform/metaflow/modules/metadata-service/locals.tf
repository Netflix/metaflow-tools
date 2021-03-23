locals {
  # Name of ECS cluster.
  ecs_cluster_name = "${var.resource_prefix}-${var.resource_suffix}"

  # Name of Fargate security group used by the Metadata Service
  metadata_service_security_group_name = "${var.resource_prefix}-metadata-service-security-group-${var.resource_suffix}"
}