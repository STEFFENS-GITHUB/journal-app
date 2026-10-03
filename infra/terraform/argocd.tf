resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "10.9.4"
  namespace        = "argocd"
  create_namespace = true

  values = [yamlencode({
    global = {
      nodeSelector = local.control_node_selector
      tolerations  = local.control_tolerations
    }
    configs = {
      params = {
        "server.insecure" = true
      }
      cm = {
        url = "https://argocd.${var.env}.${var.domain}"
      }
    }
    controller = {
      resources = {
        requests = { cpu = "100m", memory = "512Mi" }
        limits   = { memory = "1Gi" }
      }
    }
    repoServer = {
      resources = {
        requests = { cpu = "50m", memory = "256Mi" }
        limits   = { memory = "1Gi" }
      }
    }
    applicationSet = {
      resources = {
        requests = { cpu = "25m", memory = "128Mi" }
        limits   = { memory = "256Mi" }
      }
    }
    redis = {
      resources = {
        requests = { cpu = "25m", memory = "64Mi" }
        limits   = { memory = "256Mi" }
      }
    }
    redisSecretInit = {
      resources = {
        requests = { cpu = "10m", memory = "32Mi" }
        limits   = { memory = "64Mi" }
      }
    }
    dex = {
      resources = {
        requests = { cpu = "10m", memory = "64Mi" }
        limits   = { memory = "128Mi" }
      }
    }
    notifications = {
      resources = {
        requests = { cpu = "10m", memory = "64Mi" }
        limits   = { memory = "128Mi" }
      }
    }
    server = {
      resources = {
        requests = { cpu = "25m", memory = "128Mi" }
        limits   = { memory = "256Mi" }
      }
      ingress = {
        enabled          = true
        ingressClassName = "alb"
        hostname         = "argocd.${var.env}.${var.domain}"
        annotations = {
          "alb.ingress.kubernetes.io/scheme"           = "internet-facing"
          "alb.ingress.kubernetes.io/target-type"      = "ip"
          "alb.ingress.kubernetes.io/listen-ports"     = jsonencode([{ HTTP = 80 }, { HTTPS = 443 }])
          "alb.ingress.kubernetes.io/ssl-redirect"     = "443"
          "alb.ingress.kubernetes.io/healthcheck-path" = "/healthz"
        }
      }
    }
  })]

  set_wo = [
    {
      name  = "configs.secret.argocdServerAdminPassword"
      value = bcrypt(ephemeral.random_password.argocd_admin.result)
      type  = "string"
    }
  ]
  set_wo_revision = 1
  reuse_values    = true

  depends_on = [
    aws_eks_node_group.control,
    aws_eks_addon.coredns,
    aws_eks_access_policy_association.admin,
    aws_eks_access_policy_association.terraform_ci,
  ]
}

resource "helm_release" "root_app" {
  name       = "root-app"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argocd-apps"
  version    = "2.0.6"
  namespace  = helm_release.argocd.namespace

  values = [yamlencode({
    applications = {
      root-app = {
        namespace = helm_release.argocd.namespace
        project   = "default"
        source = {
          repoURL        = "https://github.com/STEFFENS-GITHUB/journal-app.git"
          targetRevision = "main"
          path           = "infra/helm/root-app"
        }
        destination = {
          server    = "https://kubernetes.default.svc"
          namespace = helm_release.argocd.namespace
        }
        syncPolicy = {
          automated = {
            prune    = true
            selfHeal = true
          }
        }
      }
    }
  })]

  depends_on = [kubernetes_secret_v1.argocd_cluster]
}

resource "terraform_data" "delete_ingresses" {
  input = aws_eks_cluster.main.name

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      set -e
      aws eks update-kubeconfig --name ${self.input} --region us-east-1
      kubectl -n argocd scale statefulset argocd-application-controller --replicas=0
      kubectl delete ingress --all --all-namespaces --wait --timeout=10m
      kubectl delete nodepool --all --wait --timeout=10m
      timeout 900 sh -c 'while kubectl get nodeclaims -o name | grep -q .; do sleep 10; done'
    EOT
  }

  depends_on = [
    helm_release.root_app,
    aws_eks_node_group.control,
    aws_eks_addon.pod_identity_agent,
    aws_eks_addon.vpc_cni,
    aws_eks_addon.kube_proxy,
    aws_eks_addon.coredns,
    module.vpc,
    aws_route.private_nat,
    module.lb_controller_pod_identity,
    module.external_dns_pod_identity,
    module.karpenter,
  ]
}

resource "kubernetes_secret_v1" "argocd_cluster" {
  metadata {
    name      = "root-app-cluster-config"
    namespace = helm_release.argocd.namespace

    labels = {
      "argocd.argoproj.io/secret-type" = "cluster"
      env                              = var.env
    }

    annotations = {
      cluster_name = aws_eks_cluster.main.name
      region       = "us-east-1"
      vpc_id       = module.vpc.vpc_id
      domain       = "${var.env}.${var.domain}"
      redis_url    = "rediss://${aws_elasticache_serverless_cache.valkey.endpoint[0].address}:${aws_elasticache_serverless_cache.valkey.endpoint[0].port}"
      queue_url    = aws_sqs_queue.journal_queue.url
      db_endpoint  = aws_rds_cluster.aurora.endpoint
      db_name      = aws_rds_cluster.aurora.database_name

      karpenter_queue = module.karpenter.queue_name
      node_role       = module.karpenter.node_iam_role_name

      db_secret_arn  = aws_rds_cluster.aurora.master_user_secret[0].secret_arn
      jwt_secret_arn = aws_secretsmanager_secret.api_jwt_signing_key.arn
    }
  }

  data = { # If remote-cluster rather then the one argo lives in, must have credentials here.
    name   = aws_eks_cluster.main.name
    server = "https://kubernetes.default.svc"
  }
}
