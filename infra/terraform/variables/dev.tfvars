env                 = "dev"
domain              = "steffenaws.com"
admin_role_arn      = "arn:aws:iam::476140239102:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_70ef77c60a6c0e1e"
terraform_role_name = "terraform-ci"
vpc_cidr_block      = "192.168.0.0/16"

public_subnets = [
  {
    cidr_block        = "192.168.1.0/24"
    availability_zone = "us-east-1a"
  },
  {
    cidr_block        = "192.168.2.0/24"
    availability_zone = "us-east-1b"
  }
]

private_subnets = [
  {
    cidr_block        = "192.168.100.0/24"
    availability_zone = "us-east-1a"
  },
  {
    cidr_block        = "192.168.101.0/24"
    availability_zone = "us-east-1b"
  }
]
