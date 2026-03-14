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
  ])

  service            = each.value
  disable_on_destroy = false
}

# =============================================================================
# Cloud Run — API (Bun + Hono)
# =============================================================================

resource "google_cloud_run_v2_service" "api" {
  name     = "${var.app_name}-api"
  location = var.region

  template {
    service_account = google_service_account.cloud_run_api.email

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
        name  = "AI_SERVICE_URL"
        value = google_cloud_run_v2_service.ai.uri
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

  depends_on = [google_project_service.services]
}

# =============================================================================
# Cloud Run — AI Processing (Python + Litestar)
# =============================================================================

resource "google_cloud_run_v2_service" "ai" {
  name     = "${var.app_name}-ai"
  location = var.region

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

      # Qdrant connection
      env {
        name = "QDRANT_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app_secrets["qdrant_url"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "QDRANT_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app_secrets["qdrant_api_key"].secret_id
            version = "latest"
          }
        }
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

  depends_on = [google_project_service.services]
}

# =============================================================================
# Cloud Run — public access (controlled by Bearer token via API Gateway later)
# For demo: allow unauthenticated (toggle with min_instances=1 for warm-up)
# =============================================================================

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# AI Processing is NOT public — only API can invoke it
# (see iam.tf: api_invokes_ai)
