# Core addons: EKS installs these self-managed on cluster creation; OVERWRITE adopts
# them as managed addons. vpc-cni uses the node role's AmazonEKS_CNI_Policy.
resource "aws_eks_addon" "vpc_cni" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "vpc-cni"
  resolve_conflicts_on_create = "OVERWRITE"

  # Assign /28 prefixes to ENIs instead of individual IPs, raising pods per node
  configuration_values = jsonencode({
    env = {
      ENABLE_PREFIX_DELEGATION = "true"
      WARM_PREFIX_TARGET       = "1"
    }
  })

  tags = {
    Environment = var.env
  }
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "kube-proxy"
  resolve_conflicts_on_create = "OVERWRITE"

  tags = {
    Environment = var.env
  }
}

resource "aws_eks_addon" "coredns" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "coredns"
  resolve_conflicts_on_create = "OVERWRITE"

  configuration_values = jsonencode({
    nodeSelector = local.control_node_selector
    tolerations  = local.control_tolerations
  })

  tags = {
    Environment = var.env
  }

  depends_on = [aws_eks_node_group.control]
}

resource "aws_eks_addon" "pod_identity_agent" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "eks-pod-identity-agent"

  tags = {
    Environment = var.env
  }

  depends_on = [aws_eks_node_group.control]
}

resource "aws_eks_addon" "metrics_server" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "metrics-server"

  configuration_values = jsonencode({
    nodeSelector = local.control_node_selector
    tolerations  = local.control_tolerations
  })

  tags = {
    Environment = var.env
  }

  depends_on = [aws_eks_node_group.control]
}

resource "aws_eks_addon" "cloudwatch_observability" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "amazon-cloudwatch-observability"

  configuration_values = jsonencode({
    manager = {
      nodeSelector = local.control_node_selector
      tolerations  = local.control_tolerations
    }
  })

  tags = {
    Environment = var.env
  }

  depends_on = [
    aws_eks_node_group.control,
    aws_eks_addon.pod_identity_agent,
    module.cloudwatch_pod_identity,
    aws_cloudwatch_log_group.container_insights,
  ]
}
