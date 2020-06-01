/*
 Allocate container management service where container could be docker
 containers for example.
*/
resource "aws_ecs_cluster" "metaflow_cluster" {
  name = var.ecs_cluster_name

  tags = {
    Name     = var.ecs_cluster_name
    Metaflow = "true"
  }
}

/*
 Define firewall for metaflow service.
*/
resource "aws_security_group" "metaflow_service" {
  name   = var.service_security_group_name
  vpc_id = aws_vpc.metaflow.id

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.my_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # all
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Metaflow = "true"
  }
}

resource "aws_ecs_task_definition" "metaflow_service_task" {
  family = "metaflow_service" # Unique name for task definition

  container_definitions = <<EOF
[
  {
    "name": "metaflow_service",
    "image": "netflixoss/metaflow_metadata_service",
    "essential": true,
    "portMappings": [
      {
        "containerPort": 8080,
        "hostPort": 8080
      }
    ],
    "environment": [
      {"name": "MF_METADATA_DB_HOST", "value": "${replace(aws_db_instance.metaflow.endpoint, ":5432", "")}"},
      {"name": "MF_METADATA_DB_NAME", "value": "metaflow"},
      {"name": "MF_METADATA_DB_PORT", "value": "5432"},
      {"name": "MF_METADATA_DB_PSWD", "value": "${var.db_password}"},
      {"name": "MF_METADATA_DB_USER", "value": "${var.db_username}"}
    ]
  }
]
EOF

  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE", "EC2"]
  task_role_arn            = aws_iam_role.iam_s3_access_role.arn
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  cpu                      = 512
  memory                   = 1024

  tags = {
    Metaflow = "true"
  }
}

resource "aws_ecs_service" "metaflow_service" {
  name            = "metaflow_service"
  cluster         = aws_ecs_cluster.metaflow_cluster.id
  task_definition = aws_ecs_task_definition.metaflow_service_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  depends_on      = [aws_iam_role.iam_s3_access_role]
  network_configuration {
    security_groups  = [aws_security_group.metaflow_service.id]
    assign_public_ip = true
    subnets          = [aws_subnet.metaflow_batch.id, aws_subnet.metaflow_ecs.id]
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}
