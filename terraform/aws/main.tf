terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.environment}-vpc"
  cidr = var.vpc_cidr

  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway = true
  single_nat_gateway = var.environment == "prod" ? false : true

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${var.environment}-eks"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = var.node_group_desired_size
      min_size     = var.node_group_min_size
      max_size     = var.node_group_max_size

      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      tags = {
        Environment = var.environment
        NodeGroup   = "general"
      }
    }

    spot = {
      desired_size = var.spot_node_group_desired_size
      min_size     = var.spot_node_group_min_size
      max_size     = var.spot_node_group_max_size

      instance_types = var.spot_instance_types
      capacity_type  = "SPOT"

      tags = {
        Environment = var.environment
        NodeGroup   = "spot"
      }
    }
  }

  # Fargate profile for serverless workloads
  fargate_profiles = {
    ai_services = {
      selectors = [
        {
          namespace = "ai-infrastructure"
          labels = {
            compute-type = "fargate"
          }
        }
      ]
    }
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# RDS Database
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.environment}-db"

  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = "5432"

  vpc_security_group_ids = [aws_security_group.rds.id]

  maintenance_window = "Mon:00:00-Mon:03:00"
  backup_window      = "03:00-06:00"

  # Enhanced Monitoring
  monitoring_interval = 30
  monitoring_role_name = "${var.environment}-rds-monitoring-role"
  create_monitoring_role = true

  # Multi-AZ for production
  multi_az = var.environment == "prod"

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# ElastiCache Redis
module "redis" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 1.0"

  cluster_id      = "${var.environment}-redis"
  engine          = "redis"
  node_type       = var.redis_node_type
  num_cache_nodes = var.redis_num_nodes
  port            = 6379

  subnet_ids = module.vpc.private_subnets
  security_group_ids = [aws_security_group.redis.id]

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "backups" {
  bucket = "${var.environment}-ai-portal-backups-${random_string.suffix.result}"

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    Purpose     = "backups"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CloudFront Distribution
module "cloudfront" {
  source  = "terraform-aws-modules/cloudfront/aws"
  version = "~> 3.0"

  aliases = var.environment == "prod" ? ["api.ai-infrastructure-portal.com"] : ["api-${var.environment}.ai-infrastructure-portal.com"]

  comment             = "AI Infrastructure Portal - ${var.environment}"
  enabled             = true
  is_ipv6_enabled     = true
  price_class         = "PriceClass_100"
  retain_on_delete    = false
  wait_for_deployment = false

  # Origin configuration for ALB
  origin = {
    alb = {
      domain_name = module.alb.lb_dns_name
      origin_id   = "alb"

      custom_origin_config = {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }

  default_cache_behavior = {
    target_origin_id       = "alb"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods  = ["GET", "HEAD"]

    compress = true

    forwarded_values = {
      query_string = true
      cookies = {
        forward = "all"
      }
    }

    lambda_function_association = var.environment == "prod" ? [
      {
        event_type   = "viewer-request"
        lambda_arn   = aws_lambda_function.waf_integration[0].qualified_arn
        include_body = false
      }
    ] : []
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Application Load Balancer
module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 8.0"

  name = "${var.environment}-alb"

  load_balancer_type = "application"
  vpc_id             = module.vpc.vpc_id
  subnets            = module.vpc.public_subnets
  security_groups    = [aws_security_group.alb.id]

  target_groups = [
    {
      name_prefix      = "api-"
      backend_protocol = "HTTP"
      backend_port     = 5001
      target_type      = "ip"

      health_check = {
        enabled             = true
        interval            = 30
        path                = "/api/health"
        port                = "traffic-port"
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 6
        protocol            = "HTTP"
        matcher             = "200-299"
      }
    },
    {
      name_prefix      = "dash-"
      backend_protocol = "HTTP"
      backend_port     = 8081
      target_type      = "ip"

      health_check = {
        enabled             = true
        interval            = 30
        path                = "/health"
        port                = "traffic-port"
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 6
        protocol            = "HTTP"
        matcher             = "200-299"
      }
    }
  ]

  https_listeners = [
    {
      port               = 443
      protocol           = "HTTPS"
      certificate_arn    = aws_acm_certificate.alb.arn
      target_group_index = 0
    }
  ]

  http_tcp_listeners = [
    {
      port        = 80
      protocol    = "HTTP"
      action_type = "redirect"
      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  ]

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "${var.environment}-alb-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.environment}-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.environment}-redis-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

resource "aws_security_group" "eks_nodes" {
  name_prefix = "${var.environment}-eks-nodes-"
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# ACM Certificate
resource "aws_acm_certificate" "alb" {
  domain_name       = var.environment == "prod" ? "api.ai-infrastructure-portal.com" : "api-${var.environment}.ai-infrastructure-portal.com"
  validation_method = "DNS"

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# WAF (Production only)
resource "aws_wafv2_web_acl" "main" {
  count = var.environment == "prod" ? 1 : 0

  name        = "${var.environment}-waf"
  description = "WAF for AI Infrastructure Portal"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      count {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.environment}-waf-metrics"
    sampled_requests_enabled   = true
  }
}

# Lambda@Edge for WAF integration
resource "aws_lambda_function" "waf_integration" {
  count = var.environment == "prod" ? 1 : 0

  filename         = data.archive_file.waf_integration[0].output_path
  function_name    = "${var.environment}-waf-integration"
  role            = aws_iam_role.lambda_edge[0].arn
  handler         = "index.handler"
  runtime         = "nodejs18.x"
  publish         = true

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Route 53 Records
resource "aws_route53_record" "api" {
  zone_id = var.route53_zone_id
  name    = var.environment == "prod" ? "api.ai-infrastructure-portal.com" : "api-${var.environment}.ai-infrastructure-portal.com"
  type    = "A"

  alias {
    name                   = module.cloudfront.cloudfront_distribution_domain_name
    zone_id               = module.cloudfront.cloudfront_distribution_hosted_zone_id
    evaluate_target_health = false
  }
}

# Random suffix for S3 bucket
resource "random_string" "suffix" {
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}

# Data sources
data "archive_file" "waf_integration" {
  count = var.environment == "prod" ? 1 : 0

  type        = "zip"
  source_file = "${path.module}/lambda/waf-integration.js"
  output_path = "${path.module}/lambda/waf-integration.zip"
}

# IAM Roles
resource "aws_iam_role" "lambda_edge" {
  count = var.environment == "prod" ? 1 : 0

  name = "${var.environment}-lambda-edge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "edgelambda.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.cloudfront_distribution_id
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.lb_dns_name
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_instance_address
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.elasticache_replication_group_primary_endpoint_address
}

output "s3_backup_bucket" {
  description = "S3 backup bucket name"
  value       = aws_s3_bucket.backups.bucket
}
