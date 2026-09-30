data "aws_route53_zone" "env" {
  name         = "${var.env}.${var.domain}"
  private_zone = false
}

data "aws_iam_role" "terraform_ci" {
  name = var.terraform_role_name
}
