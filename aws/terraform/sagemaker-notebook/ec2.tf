resource "aws_security_group" "sagemaker" {
  name = "${local.resource_prefix}-sagemaker-security-group-${local.resource_suffix}"

  description = "Sagemaker notebook security group"

  vpc_id = data.terraform_remote_state.infra.outputs.vpc_id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
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
