provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = ">= 1.10" # use_lockfile requires 1.10+

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket       = "dev-terraform-state-476140239102"
    key          = "backend/journal/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}
