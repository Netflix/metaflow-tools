/*
 Grant us ability to yield different availability zones for a region
*/
data "aws_availability_zones" "available" {
  state = "available"
}
