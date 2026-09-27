# The VPC and subnets are owned by core-infrastructure; look them up by the
# Name tags its vpc module sets (<env>-vpc, <env>-vpc-public-<az>, <env>-vpc-private-<az>).
data "aws_vpc" "main" {
  tags = {
    Name = "${var.env}-vpc"
  }
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["${var.env}-vpc-public-*"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["${var.env}-vpc-private-*"]
  }
}
