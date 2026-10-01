module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.6.1"

  name = "${var.env}-vpc"
  cidr = var.vpc_cidr_block

  # Subnets are matched to AZs by position, so each list is given in AZ order
  azs             = [for subnet in var.public_subnets : subnet.availability_zone]
  public_subnets  = [for subnet in var.public_subnets : subnet.cidr_block]
  private_subnets = [for subnet in var.private_subnets : subnet.cidr_block]

  # Subnet discovery for the AWS Load Balancer Controller
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "karpenter.sh/discovery"          = "${var.env}-journal-cluster"
  }

  # Instances launched into the public subnets get a public IP automatically
  map_public_ip_on_launch = true

  # NAT is provided by the regional gateway below; single_nat_gateway keeps
  # one private route table shared by every private subnet.
  enable_nat_gateway = false
  single_nat_gateway = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  # Leave the VPC's AWS-created defaults out of state
  manage_default_security_group = false
  manage_default_network_acl    = false
  manage_default_route_table    = false

  tags = {
    Environment = var.env
  }
}

# Regional NAT gateway: one gateway serving every AZ in the VPC, with public IPs
# auto-provisioned per AZ. Gives the private subnets egress for the nodes.
resource "aws_nat_gateway" "main" {
  vpc_id            = module.vpc.vpc_id
  availability_mode = "regional"

  tags = {
    Name        = "${var.env}-journal-nat"
    Environment = var.env
  }
}

resource "aws_route" "private_nat" {
  route_table_id         = module.vpc.private_route_table_ids[0]
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main.id
}
