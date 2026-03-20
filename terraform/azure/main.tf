terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "${var.environment}-ai-portal-rg"
  location = var.location

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "vnet" {
  name                = "${var.environment}-vnet"
  address_space       = [var.vnet_address_space]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

resource "azurerm_subnet" "private" {
  name                 = "${var.environment}-private-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.private_subnet_prefix]
}

resource "azurerm_subnet" "public" {
  name                 = "${var.environment}-public-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.public_subnet_prefix]
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.environment}-aks"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "${var.environment}-aks"

  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.vm_size
    vnet_subnet_id      = azurerm_subnet.private.id
    enable_auto_scaling = true
    min_count           = var.min_node_count
    max_count           = var.max_node_count

    tags = {
      Environment = var.environment
      NodePool    = "default"
      ManagedBy   = "terraform"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
    network_policy    = "azure"
  }

  # Enable Azure Policy
  azure_policy_enabled = true

  # Enable Azure Monitor
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.insights.id
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Azure Database for PostgreSQL
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                = "${var.environment}-postgres"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  version             = "15"
  sku_name            = var.db_sku_name
  storage_mb          = var.db_storage_mb

  administrator_login    = var.db_admin_username
  administrator_password = var.db_admin_password

  backup_retention_days = 7

  delegated_subnet_id = azurerm_subnet.private.id
  private_dns_zone_id = azurerm_private_dns_zone.postgres.id

  high_availability {
    mode = var.environment == "prod" ? "ZoneRedundant" : "Disabled"
  }

  maintenance_window {
    day_of_week  = 1
    start_hour   = 3
    start_minute = 0
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

resource "azurerm_postgresql_flexible_server_database" "ai_portal" {
  name      = var.db_name
  server_id = azurerm_postgresql_flexible_server.postgres.id
  charset   = "utf8"
  collation = "en_US.utf8"
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "redis" {
  name                = "${var.environment}-redis"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  capacity            = var.redis_capacity
  family              = var.redis_family
  sku_name            = var.redis_sku_name
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {
    maxmemory_policy = "allkeys-lru"
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Storage Account
resource "azurerm_storage_account" "backups" {
  name                     = "${var.environment}aiportalbackups${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  account_kind             = "StorageV2"

  blob_properties {
    versioning_enabled  = true
    change_feed_enabled = true

    delete_retention_policy {
      days = 90
    }

    container_delete_retention_policy {
      days = 7
    }
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    Purpose     = "backups"
    ManagedBy   = "terraform"
  }
}

resource "azurerm_storage_container" "backups" {
  name                  = "backups"
  storage_account_name  = azurerm_storage_account.backups.name
  container_access_type = "private"
}

# Application Gateway (Load Balancer)
resource "azurerm_public_ip" "appgw" {
  name                = "${var.environment}-appgw-pip"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

resource "azurerm_application_gateway" "appgw" {
  name                = "${var.environment}-appgw"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  sku {
    name     = var.appgw_sku_name
    tier     = var.appgw_sku_tier
    capacity = var.appgw_capacity
  }

  gateway_ip_configuration {
    name      = "appgw-ip-config"
    subnet_id = azurerm_subnet.public.id
  }

  frontend_port {
    name = "http-port"
    port = 80
  }

  frontend_port {
    name = "https-port"
    port = 443
  }

  frontend_ip_configuration {
    name                 = "appgw-frontend-ip"
    public_ip_address_id = azurerm_public_ip.appgw.id
  }

  backend_address_pool {
    name = "api-backend-pool"
  }

  backend_address_pool {
    name = "dashboard-backend-pool"
  }

  backend_http_settings {
    name                  = "api-http-settings"
    cookie_based_affinity = "Disabled"
    port                  = 5001
    protocol              = "Http"
    request_timeout       = 30

    probe_name = "api-health-probe"
  }

  backend_http_settings {
    name                  = "dashboard-http-settings"
    cookie_based_affinity = "Disabled"
    port                  = 8081
    protocol              = "Http"
    request_timeout       = 30

    probe_name = "dashboard-health-probe"
  }

  http_listener {
    name                           = "api-listener"
    frontend_ip_configuration_name = "appgw-frontend-ip"
    frontend_port_name             = "https-port"
    protocol                       = "Https"
    ssl_certificate_name           = "api-cert"
    host_name                      = "api.ai-infrastructure-portal.com"
  }

  http_listener {
    name                           = "dashboard-listener"
    frontend_ip_configuration_name = "appgw-frontend-ip"
    frontend_port_name             = "https-port"
    protocol                       = "Https"
    ssl_certificate_name           = "api-cert"
    host_name                      = "dashboard.ai-infrastructure-portal.com"
  }

  request_routing_rule {
    name                       = "api-routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "api-listener"
    backend_address_pool_name  = "api-backend-pool"
    backend_http_settings_name = "api-http-settings"
    priority                   = 100
  }

  request_routing_rule {
    name                       = "dashboard-routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "dashboard-listener"
    backend_address_pool_name  = "dashboard-backend-pool"
    backend_http_settings_name = "dashboard-http-settings"
    priority                   = 200
  }

  probe {
    name                = "api-health-probe"
    host                = "api.ai-infrastructure-portal.com"
    protocol            = "Http"
    path                = "/api/health"
    interval            = 30
    timeout             = 30
    unhealthy_threshold = 3
    port                = 5001
  }

  probe {
    name                = "dashboard-health-probe"
    host                = "dashboard.ai-infrastructure-portal.com"
    protocol            = "Http"
    path                = "/health"
    interval            = 30
    timeout             = 30
    unhealthy_threshold = 3
    port                = 8081
  }

  ssl_certificate {
    name     = "api-cert"
    key_vault_secret_id = azurerm_key_vault_certificate.api_cert.secret_id
  }

  waf_configuration {
    enabled          = true
    firewall_mode    = "Detection"
    rule_set_type    = "OWASP"
    rule_set_version = "3.2"
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Azure Monitor
resource "azurerm_log_analytics_workspace" "insights" {
  name                = "${var.environment}-insights"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

# Key Vault for SSL certificates
resource "azurerm_key_vault" "kv" {
  name                = "${var.environment}-ai-portal-kv"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    certificate_permissions = [
      "Create",
      "Delete",
      "Get",
      "Import",
      "List",
      "Update"
    ]

    key_permissions = [
      "Create",
      "Delete",
      "Get",
      "List",
      "Update"
    ]

    secret_permissions = [
      "Delete",
      "Get",
      "List",
      "Set"
    ]
  }

  tags = {
    Environment = var.environment
    Project     = "ai-infrastructure-portal"
    ManagedBy   = "terraform"
  }
}

resource "azurerm_key_vault_certificate" "api_cert" {
  name         = "api-cert"
  key_vault_id = azurerm_key_vault.kv.id

  certificate_policy {
    issuer_parameters {
      name = "Self"
    }

    key_properties {
      exportable = true
      key_type   = "RSA"
      key_size   = 2048
      reuse_key  = true
    }

    lifetime_action {
      action {
        action_type = "AutoRenew"
      }

      trigger {
        days_before_expiry = 30
      }
    }

    secret_properties {
      content_type = "application/x-pkcs12"
    }

    x509_certificate_properties {
      key_usage = [
        "cRLSign",
        "dataEncipherment",
        "digitalSignature",
        "keyAgreement",
        "keyCertSign",
        "keyEncipherment"
      ]

      subject_alternative_names {
        dns_names = [
          "api.ai-infrastructure-portal.com",
          "dashboard.ai-infrastructure-portal.com"
        ]
      }

      subject            = "CN=api.ai-infrastructure-portal.com"
      validity_in_months = 12
    }
  }
}

# Private DNS Zone
resource "azurerm_private_dns_zone" "postgres" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "${var.environment}-postgres-dns-link"
  resource_group_name   = azurerm_resource_group.rg.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

# Data sources
data "azurerm_client_config" "current" {}

# Random suffix
resource "random_string" "suffix" {
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}

# Outputs
output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.rg.name
}

output "aks_cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "aks_cluster_endpoint" {
  description = "AKS cluster endpoint"
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].host
}

output "appgw_public_ip" {
  description = "Application Gateway public IP"
  value       = azurerm_public_ip.appgw.ip_address
}

output "postgres_server" {
  description = "PostgreSQL server FQDN"
  value       = azurerm_postgresql_flexible_server.postgres.fqdn
}

output "redis_hostname" {
  description = "Redis cache hostname"
  value       = azurerm_redis_cache.redis.hostname
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.backups.name
}
