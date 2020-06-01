/*
 Permissions for all the resources.
*/
resource "aws_iam_role" "ecs_execution_role" {
  name               = "metaflow_ecs_execution_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "ec2.amazonaws.com",
          "ecs.amazonaws.com",
          "ecs-tasks.amazonaws.com",
          "batch.amazonaws.com"
        ]
      }
    }
  ]
}
EOF
}

/*
 Create IAM role for ECS instances similar to above.
*/
resource "aws_iam_role" "ecs_instance_role" {
  name = var.ecs_instance_role_name

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
        "Service": "ec2.amazonaws.com"
        }
    }
    ]
}
EOF
}

/*
 Attach policy AmazonEC2ContainerServiceforEC2Role to ecs_instance_role. The
 policy is what the role is allowed to do similar to rwx for a user.
 AmazonEC2ContainerServiceforEC2Role is a predefined set of permissions by aws the
 permissions given are at:
 https://docs.aws.amazon.com/AmazonECS/latest/developerguide/instance_IAM_role.html
*/
resource "aws_iam_role_policy_attachment" "ecs_instance_role" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

/*
 Instance profile is a container for an IAM role. On console when we define role
 instance profile is generated but here we have to manually generate. The instance
 profile passes role info to the instance when it starts.
 Ref:
 https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html
*/
resource "aws_iam_instance_profile" "ecs_instance_role" {
  name = var.ecs_instance_role_name
  role = aws_iam_role.ecs_instance_role.name
}

/*
 Create a role for batch service and assign it to batch and s3.
*/
resource "aws_iam_role" "aws_batch_service_role" {
  name = var.batch_service_role_name

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
          "Service": [
            "batch.amazonaws.com",
            "s3.amazonaws.com"
          ]
        }
    }
    ]
}
EOF
}

/*
 Assign permissions to role defined above. The specific permissions are at
 https://docs.aws.amazon.com/batch/latest/userguide/service_IAM_role.html
*/
resource "aws_iam_role_policy_attachment" "aws_batch_service_role" {
  role       = aws_iam_role.aws_batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

/*
 Define security group (firewall) that allows outgoing packets to any addr
 for instances in aws_vpc.metaflow.id
 depends_on tells terraform to provision aws_vpc.metaflow resource first.
*/
resource "aws_security_group" "metaflow_batch" {
  name       = var.batch_security_group_name
  description = "Allow traffic to pass from the subnet to internet"
  vpc_id     = aws_vpc.metaflow.id
  depends_on = [aws_vpc.metaflow]

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

/*
 Define new role for s3 access.
*/
resource "aws_iam_role" "iam_s3_access_role" {
  name               = "metaflow_iam_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "ec2.amazonaws.com",
          "ecs.amazonaws.com",
          "ecs-tasks.amazonaws.com",
          "batch.amazonaws.com",
          "s3.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

  tags = {
    Metaflow = "true"
  }
}

/*
 Attach permissions to the role defined above. Any of the services can call
 s3:* if target is in Resource below.
*/
resource "aws_iam_role_policy" "iam_s3_access_policy" {
  name = "metaflow_s3_access"
  role = aws_iam_role.iam_s3_access_role.name

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
        "Sid": "ListObjectsInBucket",
        "Effect": "Allow",
        "Action": ["s3:*"],
        "Resource": ["${aws_s3_bucket.metaflow.arn}", "${aws_s3_bucket.metaflow.arn}/*"]
    }
  ]
}
EOF
}

/*
 For any entity that has the role specified give permissions to run the actions
 listed for any resource.
*/
resource "aws_iam_role_policy" "ecs_execution_policy" {
  name   = "metaflow_ecs_execution_policy"
  role   = aws_iam_role.ecs_execution_role.name
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "s3:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}
