# =============================================================================
# Enable required GCP APIs
# =============================================================================

resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "firebase.googleapis.com",
    "firebasehosting.googleapis.com",
    "sqladmin.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Wait for API enablement to propagate across GCP systems (~60s)
resource "time_sleep" "api_propagation" {
  create_duration = "60s"
  depends_on      = [google_project_service.services]
}

# =============================================================================
# Cloud Run — Gateway (Bun + Hono) — sole public entry point
# =============================================================================

resource "google_cloud_run_v2_service" "gateway" {
  name     = "${var.app_name}-gateway"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL" # Public entry point

  template {
    service_account = google_service_account.cloud_run_gateway.email

    scaling {
      min_instance_count = var.gateway_min_instances
      max_instance_count = var.gateway_max_instances
    }

    containers {
      image = var.gateway_image

      resources {
        limits = {
          memory = var.gateway_memory
          cpu    = var.gateway_cpu
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      # Gateway proxies to Backend (API) service
      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.api.uri
      }

      liveness_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 3
        period_seconds        = 30
      }

      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 2
        period_seconds        = 5
        failure_threshold     = 10
      }
    }
  }

  depends_on = [time_sleep.api_propagation]
}

# =============================================================================
# Cloud Run — API (Bun + Hono) — internal only (via Gateway)
# =============================================================================

resource "google_cloud_run_v2_service" "api" {
  name     = "${var.app_name}-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL" # Public (Gateway proxy does not add identity tokens; JWT auth enforced at app level)

  template {
    service_account = google_service_account.cloud_run_api.email

    # Cloud SQL Auth Proxy: secure connection via Unix socket (no VPC needed)
    annotations = {
      "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.main.connection_name
    }

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = var.api_max_instances
    }

    containers {
      image = var.api_image

      resources {
        limits = {
          memory = var.api_memory
          cpu    = var.api_cpu
        }
        cpu_idle          = true   # CPU only allocated during request (cost saving)
        startup_cpu_boost = true   # Faster cold start
      }

      # Inject AI Processing URL so API can call it
      env {
        name  = "APP_ENV"
        value = var.environment
      }

      env {
        name  = "AI_PROCESSING_URL"
        value = google_cloud_run_v2_service.ai.uri
      }

      # JWT signing secret from Secret Manager
      env {
        name = "JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app_secrets["jwt_secret"].secret_id
            version = "latest"
          }
        }
      }

      # Database connection URL (Cloud SQL Auth Proxy Unix socket)
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      # Liveness probe
      liveness_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 5
        period_seconds        = 30
      }

      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 3
        period_seconds        = 5
        failure_threshold     = 10
      }
    }
  }

  depends_on = [time_sleep.api_propagation]
}

# =============================================================================
# Cloud Run — AI Processing (Python + Litestar)
# =============================================================================

resource "google_cloud_run_v2_service" "ai" {
  name     = "${var.app_name}-ai"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY" # Internal only (via Backend)

  template {
    service_account = google_service_account.cloud_run_ai.email

    scaling {
      min_instance_count = var.ai_min_instances
      max_instance_count = var.ai_max_instances
    }

    containers {
      image = var.ai_image

      resources {
        limits = {
          memory = var.ai_memory
          cpu    = var.ai_cpu
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      # Read OpenAI API key from Secret Manager
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app_secrets["openai_api_key"].secret_id
            version = "latest"
          }
        }
      }

      # Qdrant connection (GCE instance — Terraform-managed static IP)
      # Not a secret: no API key, public Coursera data only.
      # TODO: move to VPC internal networking for tighter security
      env {
        name  = "QDRANT_URL"
        value = "http://${google_compute_address.qdrant.address}:6333"
      }

      liveness_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 15  # Python + ML libs take longer
        period_seconds        = 30
      }

      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 10
        period_seconds        = 10
        failure_threshold     = 20  # Allow up to 200s for cold start
      }
    }
  }

  depends_on = [time_sleep.api_propagation]
}

# =============================================================================
# Cloud Run — public access: Gateway only
# =============================================================================

resource "google_cloud_run_v2_service_iam_member" "gateway_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.gateway.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# AI Processing is NOT public — access via Backend service account only
# (see iam.tf: api_invokes_ai)
