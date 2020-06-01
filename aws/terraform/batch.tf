resource "aws_batch_compute_environment" "metaflow" {
  /* Unique name for compute environment*/
  compute_environment_name = var.compute_env_name

  compute_resources {
    /* Give permissions so the ECS container instances can make API call. */
    instance_role = aws_iam_instance_profile.ecs_instance_role.arn

    /* List of types that can be launched. */
    instance_type = [
      var.batch_instance_type,
    ]

    /* Range of number of CPUs. */
    max_vcpus     = var.batch_max_cpu
    min_vcpus     = var.batch_min_cpu
    desired_vcpus = var.batch_min_cpu

    /* Security group to apply to the instances launched. */
    security_group_ids = [
      aws_security_group.metaflow_batch.id,
    ]

    /* Which subnet to launch the instances into. */
    subnets = [
      aws_subnet.metaflow_batch.id,
    ]

    /*
     Type of instance:
     EC2 for on-demand
     SPOT specify use an unused instance at discount if available
    */
    type = "EC2"
  }

  /* Give permissions so the batch service can make API calls. */
  service_role = aws_iam_role.aws_batch_service_role.arn
  type         = "MANAGED"
  depends_on   = [aws_iam_role_policy_attachment.aws_batch_service_role]
}

# Create the Batch Job Queue
resource "aws_batch_job_queue" "metaflow" {
  name                 = var.batch_queue_name
  state                = "ENABLED"
  priority             = 1
  compute_environments = [aws_batch_compute_environment.metaflow.arn]
}
