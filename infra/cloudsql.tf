# =============================================================================
# Cloud SQL — PostgreSQL 16 (db-f1-micro, asia-northeast1)
# Cost: ~$9.37/instance + ~$1.70/storage = ~$11/month if running full month
# Stop instance when not in use to save cost (storage still accrues ~$1.70/mo)
# =============================================================================

resource "google_sql_database_instance" "main" {
  name             = "${var.app_name}-db"
  database_version = "POSTGRES_16"
  region           = var.region

  deletion_protection = false # Allow terraform destroy

  settings {
    tier = "db-f1-micro"

    ip_configuration {
      ipv4_enabled = true # Required: Cloud Run Auth Proxy connects via public IP + IAM auth
    }

    backup_configuration {
      enabled = false # Disabled for cost (demo/capstone only)
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_sql_database" "main" {
  name     = "lumineer"
  instance = google_sql_database_instance.main.name
}

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "google_sql_user" "main" {
  name     = "lumineer"
  instance = google_sql_database_instance.main.name
  password = random_password.db.result
}

# Store DATABASE_URL in Secret Manager so Cloud Run can inject it securely
resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.app_name}-database-url"

  replication {
    auto {}
  }

  labels = {
    app = var.app_name
    env = var.environment
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id

  # Cloud Run connects via Cloud SQL Auth Proxy Unix socket
  secret_data = "postgresql://lumineer:${random_password.db.result}@localhost/lumineer?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
}
