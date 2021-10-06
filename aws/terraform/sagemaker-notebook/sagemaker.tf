resource "aws_security_group" "sagemaker" {
  name        = "${local.resource_prefix}-sagemaker-security-group-${local.resource_suffix}"
  description = "Sagemaker notebook security group"
  vpc_id      = data.terraform_remote_state.infra.outputs.vpc_id

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # egress to anywhere
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.standard_tags
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "this" {
  name = "${local.resource_prefix}-nb-instance-lc-conf-${local.resource_suffix}"

  # recreates what our outputs produces
  # this is acceptable repetition as we cannot reference our outputs until the Terraform stack is applied
  # Note: We are purposefully providing the value of METAFLOW_SERVICE_INTERNAL_URL to the key METAFLOW_SERVICE_URL
  # this way our Jupyter Notebooks will speak to our internal Load Balancer just like it is our API Gateway.
  # This ensures our Jupyter Notebook queries stay within our VPC.
  on_start = base64encode(
    <<EOF
#!/bin/bash
echo 'export METAFLOW_DATASTORE_SYSROOT_S3=s3://${data.terraform_remote_state.metaflow.outputs.metaflow_s3_bucket_name}/metaflow/' >> /etc/profile.d/jupyter-env.sh
echo 'export METAFLOW_DATATOOLS_S3ROOT=s3://${data.terraform_remote_state.metaflow.outputs.metaflow_s3_bucket_name}/data/' >> /etc/profile.d/jupyter-env.sh
echo 'export METAFLOW_SERVICE_URL=${data.terraform_remote_state.metaflow.outputs.METAFLOW_SERVICE_INTERNAL_URL}' >> /etc/profile.d/jupyter-env.sh
echo 'export AWS_DEFAULT_REGION=${var.aws_region}' >> /etc/profile.d/jupyter-env.sh
echo 'export METAFLOW_DEFAULT_DATASTORE=s3' >> /etc/profile.d/jupyter-env.sh
echo 'export METAFLOW_DEFAULT_METADATA=service' >> /etc/profile.d/jupyter-env.sh
initctl restart jupyter-server --no-wait
EOF
  )
}

resource "random_pet" "this" {
}


resource "aws_sagemaker_notebook_instance" "this" {
  # Random Pet name is added to make it easier to deploy changes to this instance without having name conflicts
  # names must be unique, so the "Random Pet" helps us here
  name = "${local.resource_prefix}-nb-inst-${random_pet.this.id}-${local.resource_suffix}"

  instance_type = var.ec2_instance_type

  role_arn = aws_iam_role.sagemaker_execution_role.arn

  lifecycle_config_name = aws_sagemaker_notebook_instance_lifecycle_configuration.this.name

  subnet_id = data.terraform_remote_state.infra.outputs.subnet1_id

  security_groups = [
    aws_security_group.sagemaker.id
  ]

  # The standard tags to apply to every AWS resource.
  tags = local.standard_tags
}
