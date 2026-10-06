resource "terraform_data" "kubernetes_cleanup" {
  input = aws_eks_cluster.main.name

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      set -e
      aws eks update-kubeconfig --name ${self.input} --region us-east-1
      kubectl -n argocd scale statefulset argocd-application-controller --replicas=0
      kubectl delete ingress --all --all-namespaces --wait --timeout=10m
      kubectl delete namespace monitoring --ignore-not-found --wait --timeout=10m
      timeout 600 sh -c 'while kubectl get pv -o name | grep -q .; do sleep 10; done'
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
    aws_eks_addon.ebs_csi_driver,
    module.ebs_csi_pod_identity,
    kubernetes_storage_class_v1.gp3,
  ]
}

resource "terraform_data" "aws_cleanup" {
  input = module.vpc.vpc_id

  provisioner "local-exec" {
    when    = destroy
    command = "${path.module}/scripts/aws-cleanup.sh ${self.input}"
  }

  depends_on = [module.vpc]
}
