# EKS Auto Mode is disabled: it is only enabled when compute_config,
# storage_config and kubernetes_network_config.elastic_load_balancing are set.
resource "aws_eks_cluster" "main" {
  name     = "${var.env}-journal-cluster"
  version  = "1.36"
  role_arn = aws_iam_role.eks_cluster.arn

  access_config {
    authentication_mode                         = "API"
    bootstrap_cluster_creator_admin_permissions = false
  }

  vpc_config {
    subnet_ids              = module.vpc.private_subnets
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  tags = {
    Environment = var.env
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster]
}

locals {
  control_node_selector = {
    "node-role" = "control"
  }
  control_tolerations = [
    {
      key      = "CriticalAddonsOnly"
      operator = "Exists"
    }
  ]
}

resource "aws_eks_node_group" "control" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.env}-journal-control"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = module.vpc.private_subnets

  scaling_config {
    desired_size = 2
    min_size     = 2
    max_size     = 2
  }

  labels = local.control_node_selector

  taint {
    key    = "CriticalAddonsOnly"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  tags = {
    Environment = var.env
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_node,
    aws_route.private_nat,
    aws_eks_addon.vpc_cni,
  ]
}

# Log groups written by the amazon-cloudwatch-observability addon (Container Insights + Fluent Bit).
# Created here so retention is managed instead of the addon creating them with no expiry.
resource "aws_cloudwatch_log_group" "container_insights" {
  for_each = toset(["application", "dataplane", "host", "performance"])

  name              = "/aws/containerinsights/${aws_eks_cluster.main.name}/${each.value}"
  retention_in_days = 1

  tags = {
    Environment = var.env
  }
}

module "cloudwatch_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.9.0"

  name                                       = "${var.env}-journal-cloudwatch-role"
  use_name_prefix                            = false
  attach_aws_cloudwatch_observability_policy = true

  associations = {
    cloudwatch = {
      cluster_name    = aws_eks_cluster.main.name
      namespace       = "amazon-cloudwatch"
      service_account = "cloudwatch-agent"
    }
  }

  tags = {
    Environment = var.env
  }
}

module "api_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.9.0"

  name            = "${var.env}-journal-api-role"
  use_name_prefix = false

  attach_custom_policy = true
  policy_statements = [
    {
      actions = [
        "sqs:SendMessage",
        "sqs:GetQueueAttributes",
      ]
      resources = [aws_sqs_queue.journal_queue.arn]
    }
  ]

  associations = {
    api = {
      cluster_name    = aws_eks_cluster.main.name
      namespace       = "journal-app"
      service_account = "api"
    }
  }

  tags = {
    Environment = var.env
  }
}

module "external_secrets_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.9.0"

  name            = "${var.env}-journal-external-secrets-role"
  use_name_prefix = false

  attach_external_secrets_policy = true
  external_secrets_secrets_manager_arns = [
    aws_rds_cluster.aurora.master_user_secret[0].secret_arn,
    aws_secretsmanager_secret.api_jwt_signing_key.arn,
  ]

  associations = {
    external_secrets = {
      cluster_name    = aws_eks_cluster.main.name
      namespace       = "external-secrets"
      service_account = "external-secrets"
    }
  }

  tags = {
    Environment = var.env
  }
}

module "worker_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.9.0"

  name            = "${var.env}-journal-worker-role"
  use_name_prefix = false

  attach_custom_policy = true
  policy_statements = [
    {
      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
      ]
      resources = [aws_sqs_queue.journal_queue.arn]
    }
  ]

  associations = {
    worker = {
      cluster_name    = aws_eks_cluster.main.name
      namespace       = "journal-app"
      service_account = "worker"
    }
  }

  tags = {
    Environment = var.env
  }
}

module "lb_controller_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.9.0"

  name            = "${var.env}-journal-lb-controller-role"
  use_name_prefix = false

  attach_aws_lb_controller_policy = true

  associations = {
    lb_controller = {
      cluster_name    = aws_eks_cluster.main.name
      namespace       = "kube-system"
      service_account = "aws-load-balancer-controller"
    }
  }

  tags = {
    Environment = var.env
  }
}

module "karpenter" {
  source  = "terraform-aws-modules/eks/aws//modules/karpenter"
  version = "21.26.0"

  cluster_name = aws_eks_cluster.main.name

  iam_role_name            = "${var.env}-journal-karpenter-role"
  iam_role_use_name_prefix = false
  enable_inline_policy     = true

  node_iam_role_name            = "${var.env}-journal-karpenter-node-role"
  node_iam_role_use_name_prefix = false
  node_iam_role_additional_policies = {
    ssm = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  }

  create_access_entry = true

  tags = {
    Environment = var.env
  }
}

module "keda_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.9.0"

  name            = "${var.env}-journal-keda-role"
  use_name_prefix = false

  attach_custom_policy = true
  policy_statements = [
    {
      actions   = ["sqs:GetQueueAttributes"]
      resources = [aws_sqs_queue.journal_queue.arn]
    }
  ]

  associations = {
    keda = {
      cluster_name    = aws_eks_cluster.main.name
      namespace       = "keda"
      service_account = "keda-operator"
    }
  }

  tags = {
    Environment = var.env
  }
}

module "external_dns_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.9.0"

  name            = "${var.env}-journal-external-dns-role"
  use_name_prefix = false

  attach_external_dns_policy    = true
  external_dns_hosted_zone_arns = [data.aws_route53_zone.env.arn]

  associations = {
    external_dns = {
      cluster_name    = aws_eks_cluster.main.name
      namespace       = "kube-system"
      service_account = "external-dns"
    }
  }

  tags = {
    Environment = var.env
  }
}

resource "aws_acm_certificate" "env" {
  domain_name               = "${var.env}.${var.domain}"
  subject_alternative_names = ["*.${var.env}.${var.domain}"]
  validation_method         = "DNS"

  tags = {
    Environment = var.env
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.env.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    } if !startswith(dvo.domain_name, "*.")
  }

  zone_id         = data.aws_route53_zone.env.zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "env" {
  certificate_arn         = aws_acm_certificate.env.arn
  validation_record_fqdns = [for r in aws_route53_record.acm_validation : r.fqdn]
}

resource "aws_eks_access_entry" "admin" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = var.admin_role_arn
  type          = "STANDARD"

  tags = {
    Environment = var.env
  }
}

resource "aws_eks_access_policy_association" "admin" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_eks_access_entry.admin.principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }
}

resource "aws_eks_access_entry" "terraform_ci" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = data.aws_iam_role.terraform_ci.arn
  type          = "STANDARD"

  tags = {
    Environment = var.env
  }
}

resource "aws_eks_access_policy_association" "terraform_ci" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_eks_access_entry.terraform_ci.principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }
}
