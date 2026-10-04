# Infrastruktur der Autovermietung in Azure
#
#   Internet --HTTPS--> Container Apps (1..5 Replicas) --TLS--> PostgreSQL Flexible Server
#                              |
#                        Log Analytics (Logs & Metriken)

locals {
  tags = {
    project = var.project
    purpose = "VICC Praxisarbeit"
  }
}

# Zufälliges Suffix, weil der DB-Servername weltweit eindeutig sein muss
resource "random_string" "suffix" {
  length  = 5
  upper   = false
  special = false
}

# DB-Passwort wird generiert und nie ins Repo geschrieben.
# Ohne Sonderzeichen, damit es ohne Kodierung in die Verbindungs-URL passt.
resource "random_password" "db" {
  length  = 32
  special = false
}

# Secret Key für die Session-Cookies (gleich für alle Replicas)
resource "random_password" "flask_secret" {
  length  = 48
  special = false
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project}"
  location = var.location
  tags     = local.tags
}

# ---------------------------------------------------------------- Monitoring
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${var.project}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

# ---------------------------------------------------------------- Datenbank (DBaaS)
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "psql-${var.project}-${random_string.suffix.result}"
  location               = azurerm_resource_group.main.location
  resource_group_name    = azurerm_resource_group.main.name
  version                = "16"
  sku_name               = var.db_sku
  storage_mb             = 32768
  backup_retention_days  = 7
  administrator_login    = "caradmin"
  administrator_password = random_password.db.result

  # IST: öffentlicher Endpunkt, per Firewall nur für Azure-Dienste offen.
  # SOLL: VNet-Integration mit privatem Endpunkt (höhere Kosten/Komplexität).
  public_network_access_enabled = true

  # Hochverfügbarkeit (Zone-redundant HA) ist im Burstable-Tier nicht verfügbar.
  # SOLL: General Purpose + high_availability { mode = "ZoneRedundant" }

  tags = local.tags

  lifecycle {
    # Azure wählt die Zone selbst; ohne ignore_changes will Terraform sie ständig ändern
    ignore_changes = [zone]
  }
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = "cardb"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Spezialregel 0.0.0.0: erlaubt Zugriffe aus Azure-Diensten (z.B. Container Apps)
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# ---------------------------------------------------------------- Container Apps (PaaS)
resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${var.project}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = local.tags
}

resource "azurerm_container_app" "web" {
  name                         = "ca-${var.project}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  # Secrets werden verschlüsselt in Container Apps gespeichert und
  # als Umgebungsvariablen in den Container gegeben.
  # SOLL: Azure Key Vault mit Managed Identity.
  secret {
    name  = "database-url"
    value = "postgresql://caradmin:${random_password.db.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.app.name}?sslmode=require"
  }

  secret {
    name  = "flask-secret-key"
    value = random_password.flask_secret.result
  }

  ingress {
    external_enabled = true # öffentlich erreichbar, HTTPS-Zertifikat durch Azure
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = "web"
      image  = "${var.container_image}:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
      env {
        name        = "SECRET_KEY"
        secret_name = "flask-secret-key"
      }
      env {
        name  = "COOKIE_SECURE"
        value = "true"
      }

      # Liveness: hängt der Prozess, wird der Container neu gestartet
      liveness_probe {
        transport     = "HTTP"
        port          = 8000
        path          = "/api/health"
        initial_delay = 10
      }

      # Readiness: Traffic nur an Instanzen mit funktionierender DB-Verbindung
      readiness_probe {
        transport = "HTTP"
        port      = 8000
        path      = "/api/ready"
      }
    }

    # Automatische Skalierung: ab 20 gleichzeitigen Requests pro Instanz
    # wird eine weitere Instanz gestartet (bis max_replicas)
    http_scale_rule {
      name                = "http-scaling"
      concurrent_requests = "20"
    }
  }
}
