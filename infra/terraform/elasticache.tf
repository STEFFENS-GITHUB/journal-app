resource "aws_security_group" "elasticache" {
  name        = "${var.env}-journal-elasticache"
  description = "ElastiCache access from EKS pods"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6380
    protocol        = "tcp"
    security_groups = [aws_eks_cluster.main.vpc_config[0].cluster_security_group_id]
  }

  tags = {
    Environment = var.env
  }
}

resource "aws_elasticache_serverless_cache" "valkey" {
  engine               = "valkey"
  name                 = "${var.env}-journal-valkey"
  major_engine_version = "8"
  subnet_ids           = module.vpc.private_subnets
  security_group_ids   = [aws_security_group.elasticache.id]

  tags = {
    Environment = var.env
  }
}
