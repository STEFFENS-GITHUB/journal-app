variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "domain" {
  description = "Base domain; resources are served under {env}.{domain}"
  type        = string
}

variable "admin_role_arn" {
  description = "IAM role ARN granted cluster admin via EKS access entry"
  type        = string
}

variable "terraform_role_name" {
  description = "Name of the IAM role Terraform runs as, granted cluster admin via EKS access entry"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "public_subnets" {
  description = "List of public subnet configurations"
  type = list(object({
    cidr_block        = string
    availability_zone = string
  }))
}

variable "private_subnets" {
  description = "List of private subnet configurations"
  type = list(object({
    cidr_block        = string
    availability_zone = string
  }))
}
