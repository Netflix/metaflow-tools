# Setup Postgres RDS instance
/*
 A subnet is attached to an availability zone so for db redundancy and
 performance we need to define additional subnet(s) and aws_db_subnet_group
 is how we define this.
*/
resource "aws_db_subnet_group" "pg_subnet_group" {
  name       = var.pg_subnet_group_name
  subnet_ids = [aws_subnet.metaflow_batch.id, aws_subnet.metaflow_ecs.id]

  tags = {
    Name     = var.pg_subnet_group_name
    Metaflow = "true"
  }
}

/*
 Define a new firewall for our database instance.
*/
resource "aws_security_group" "metaflow_db" {
  name       = var.db_security_group_name
  vpc_id     = aws_vpc.metaflow.id
  depends_on = [aws_vpc.metaflow]

  /* Accept query from port 5432. */
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.my_cidr_block]
  }

  /* Can send to any IP addr. */
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

/*
 Define rds db instance.
*/
resource "aws_db_instance" "metaflow" {
  allocated_storage         = 20 # Allocate 20GB
  storage_type              = "gp2" # general purpose SSD
  engine                    = "postgres"
  instance_class            = var.db_instance_type # Hardware configuration
  identifier                = var.db_name # used for dns hostname needs to be customer unique in region
  name                      = "metaflow" # unique id for CLI commands
  username                  = var.db_username
  password                  = var.db_password
  db_subnet_group_name      = aws_db_subnet_group.pg_subnet_group.id
  max_allocated_storage     = 1000 # Upper limit of automatic scaled storage
  multi_az                  = true # Multiple availability zone?
  final_snapshot_identifier = "${var.db_name}-final-snapshot" # Snapshot upon delete
  vpc_security_group_ids    = [aws_security_group.metaflow_db.id]

  tags = {
    Name     = var.db_name
    Metaflow = "true"
  }
}
