/*
 Creata S3 bucket for storage and define access policies which apply to whomever
 has the roles defined above. Under Resource "arn:aws:s3:::${var.bucket_name}"
 refers to bucket and "arn:aws:s3:::${var.bucket_name}/*" to its contents, * is
 wildcard. S3 is for storing objects, we can store and remove but cannot edit.
 A tag is a key value pair assigned by user to an AWS resource for keeping track
 usually ignored by aws.
 Ref
 https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html
*/
# Create a S3 bucket for storing metaflow data
# otherwise stored locally in .metaflow directory
resource "aws_s3_bucket" "metaflow" {
  bucket = var.bucket_name
  acl    = "private"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "allow-ecs-instance",
      "Effect": "Allow",
      "Principal": {
        "AWS": "${aws_iam_role.ecs_instance_role.arn}"
      },
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::${var.bucket_name}",
        "arn:aws:s3:::${var.bucket_name}/*"
      ]
    },
    {
      "Sid": "allow-ecs-execution",
      "Effect": "Allow",
      "Principal": {
        "AWS": "${aws_iam_role.ecs_execution_role.arn}"
      },
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::${var.bucket_name}",
        "arn:aws:s3:::${var.bucket_name}/*"
      ]
    },
    {
      "Sid": "allow-batch-service",
      "Effect": "Allow",
      "Principal": {
        "AWS": "${aws_iam_role.aws_batch_service_role.arn}"
      },
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::${var.bucket_name}",
        "arn:aws:s3:::${var.bucket_name}/*"
      ]
    }
  ]
}
EOF

  tags = {
    Metaflow = "true"
  }
}
