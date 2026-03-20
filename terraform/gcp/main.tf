terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.environment}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  depends_on = [google_project_service.compute]
}

resource "google_compute_subnetwork" "private" {
  name          = "${var.environment}-private-subnet"
  ip_cidr_range = var.private_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pod_subnet_cidr
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.service_subnet_cidr
  }
}

resource "google_compute_subnetwork" "public" {
  name          = "${var.environment}-public-subnet"
  ip_cidr_range = var.public_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}

# Cloud Router and NAT Gateway
resource "google_compute_router" "router" {
  name    = "${var.environment}-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.environment}-nat"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# GKE Cluster
resource "google_container_cluster" "gke" {
  name     = "${var.environment}-gke"
  location = var.region

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.private.id

  ip_allocation_policy {
    cluster_secondary_range_name  = google_compute_subnetwork.private.secondary_ip_range[0].range_name
    services_secondary_range_name = google_compute_subnetwork.private.secondary_ip_range[1].range_name
  }

  # Enable Autopilot for serverless Kubernetes
  enable_autopilot = true

  # Private cluster
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_ipv4_cidr
  }

  # Enable workload identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Enable network policy
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  # Enable binary authorization
  binary_authorization {
    evaluation_mode = "DISABLED"
  }

  # Enable shielded nodes
  enable_shielded_nodes = true

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  # Enable GKE usage metering
  resource_usage_export_config {
    enable_network_egress_metering = true
    enable_resource_consumption_metering = true

    bigquery_destination {
      dataset_id = google_bigquery_dataset.gke_usage.dataset_id
    }
  }

  depends_on = [
    google_project_service.container,
    google_project_service.compute,
    google_bigquery_dataset.gke_usage
  ]
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "postgres" {
  name             = "${var.environment}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.db_tier

    disk_size = var.db_disk_size
    disk_type = "PD_SSD"

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    maintenance_window {
      day  = 1
      hour = 3
    }

    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.vpc.id
    }

    database_flags {
      name  = "max_connections"
      value = "1000"
    }

    insights_config {
      query_insights_enabled = true
    }
  }

  depends_on = [google_project_service.sqladmin]
}

resource "google_sql_database" "ai_portal" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "ai_portal" {
  name     = var.db_username
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Memorystore Redis
resource "google_redis_instance" "redis" {
  name           = "${var.environment}-redis"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size

  region                  = var.region
  location_id             = var.zone
  alternative_location_id = var.redis_replica_zone

  redis_version = "REDIS_6_X"
  display_name  = "${var.environment} Redis Instance"

  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  depends_on = [google_project_service.redis]
}

# Cloud Storage Buckets
resource "google_storage_bucket" "backups" {
  name          = "${var.environment}-ai-portal-backups-${random_id.suffix.hex}"
  location      = var.region
  storage_class = "STANDARD"

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.bucket_key.id
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.storage]
}

# Cloud Load Balancer
resource "google_compute_global_address" "lb_ip" {
  name = "${var.environment}-lb-ip"
}

resource "google_compute_global_forwarding_rule" "lb_forwarding_rule" {
  name       = "${var.environment}-lb-forwarding-rule"
  target     = google_compute_target_https_proxy.lb_proxy.id
  port_range = "443"
  ip_address = google_compute_global_address.lb_ip.address
}

resource "google_compute_target_https_proxy" "lb_proxy" {
  name             = "${var.environment}-lb-proxy"
  url_map          = google_compute_url_map.lb_url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.lb_cert.id]
}

resource "google_compute_url_map" "lb_url_map" {
  name            = "${var.environment}-lb-url-map"
  default_service = google_compute_backend_service.api_backend.id

  host_rule {
    hosts        = ["api.ai-infrastructure-portal.com"]
    path_matcher = "api"
  }

  path_matcher {
    name            = "api"
    default_service = google_compute_backend_service.api_backend.id

    path_rule {
      paths   = ["/api/*"]
      service = google_compute_backend_service.api_backend.id
    }

    path_rule {
      paths   = ["/*"]
      service = google_compute_backend_service.dashboard_backend.id
    }
  }
}

resource "google_compute_backend_service" "api_backend" {
  name                  = "${var.environment}-api-backend"
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  timeout_sec           = 30

  backend {
    group = google_container_cluster.gke.endpoint
    balancing_mode = "UTILIZATION"
  }

  health_checks = [google_compute_health_check.api_health_check.id]
}

resource "google_compute_backend_service" "dashboard_backend" {
  name                  = "${var.environment}-dashboard-backend"
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  timeout_sec           = 30

  backend {
    group = google_container_cluster.gke.endpoint
    balancing_mode = "UTILIZATION"
  }

  health_checks = [google_compute_health_check.dashboard_health_check.id]
}

resource "google_compute_health_check" "api_health_check" {
  name = "${var.environment}-api-health-check"

  http_health_check {
    port         = 5001
    request_path = "/api/health"
  }
}

resource "google_compute_health_check" "dashboard_health_check" {
  name = "${var.environment}-dashboard-health-check"

  http_health_check {
    port         = 8081
    request_path = "/health"
  }
}

resource "google_compute_managed_ssl_certificate" "lb_cert" {
  name = "${var.environment}-lb-cert"

  managed {
    domains = ["api.ai-infrastructure-portal.com"]
  }
}

# Cloud Armor (WAF equivalent)
resource "google_compute_security_policy" "cloud_armor" {
  name = "${var.environment}-cloud-armor"

  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default rule"
  }

  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      expr {
        expression = "request.headers['user-agent'].contains('BadBot')"
      }
    }
    description = "Block bad bots"
  }

  rule {
    action   = "deny(429)"
    priority = "1001"
    match {
      expr {
        expression = "rateLimit(request.method == 'POST', 100, '1m')"
      }
    }
    description = "Rate limit POST requests"
  }
}

# BigQuery for GKE usage metering
resource "google_bigquery_dataset" "gke_usage" {
  dataset_id                  = "${var.environment}_gke_usage"
  friendly_name               = "GKE Usage Dataset"
  description                 = "Dataset for GKE usage metering"
  location                    = var.region
  default_table_expiration_ms = 31536000000 # 1 year

  depends_on = [google_project_service.bigquery]
}

# Cloud KMS for encryption
resource "google_kms_key_ring" "key_ring" {
  name     = "${var.environment}-key-ring"
  location = "global"

  depends_on = [google_project_service.kms]
}

resource "google_kms_crypto_key" "bucket_key" {
  name     = "${var.environment}-bucket-key"
  key_ring = google_kms_key_ring.key_ring.id

  purpose = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "SOFTWARE"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Cloud DNS
resource "google_dns_managed_zone" "ai_portal" {
  name        = "${var.environment}-ai-portal-zone"
  dns_name    = "ai-infrastructure-portal.com."
  description = "DNS zone for AI Infrastructure Portal"

  depends_on = [google_project_service.dns]
}

resource "google_dns_record_set" "api" {
  name = "api.${google_dns_managed_zone.ai_portal.dns_name}"
  type = "A"
  ttl  = 300

  managed_zone = google_dns_managed_zone.ai_portal.name

  rrdatas = [google_compute_global_address.lb_ip.address]
}

# Enable required APIs
resource "google_project_service" "compute" {
  service = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "container" {
  service = "container.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin" {
  service = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "redis" {
  service = "redis.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "storage" {
  service = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "bigquery" {
  service = "bigquery.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "kms" {
  service = "cloudkms.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "dns" {
  service = "dns.googleapis.com"
  disable_on_destroy = false
}

# Random ID for bucket naming
resource "random_id" "suffix" {
  byte_length = 4
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = google_compute_network.vpc.id
}

output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.gke.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.gke.endpoint
}

output "lb_ip_address" {
  description = "Load balancer IP address"
  value       = google_compute_global_address.lb_ip.address
}

output "cloud_sql_instance" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "redis_instance" {
  description = "Redis instance host"
  value       = google_redis_instance.redis.host
}

output "storage_bucket" {
  description = "Storage bucket name"
  value       = google_storage_bucket.backups.name
}
