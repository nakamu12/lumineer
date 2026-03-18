# =============================================================================
# Artifact Registry — Docker image repository
# =============================================================================

resource "google_artifact_registry_repository" "images" {
  repository_id = "${var.app_name}-images"
  format        = "DOCKER"
  location      = var.region
  description   = "Docker images for Lumineer services"

  depends_on = [time_sleep.api_propagation]
}

# =============================================================================
# Service Accounts
# =============================================================================

resource "google_service_account" "cloud_run_gateway" {
  account_id   = "${var.app_name}-gw-sa"
  display_name = "Lumineer Gateway Cloud Run SA"
  description  = "Service account for Cloud Run Gateway (Hono) service"
}

resource "google_service_account" "cloud_run_api" {
  account_id   = "${var.app_name}-api-sa"
  display_name = "Lumineer API Cloud Run SA"
  description  = "Service account for Cloud Run API (Hono) service"
}

resource "google_service_account" "cloud_run_ai" {
  account_id   = "${var.app_name}-ai-sa"
  display_name = "Lumineer AI Processing Cloud Run SA"
  description  = "Service account for Cloud Run AI Processing (Python) service"
}

resource "google_service_account" "github_actions" {
  account_id   = "${var.app_name}-gh-actions-sa"
  display_name = "Lumineer GitHub Actions SA"
  description  = "Service account for GitHub Actions CI/CD (deploy + push images)"
}

# =============================================================================
# IAM — Gateway service account
# =============================================================================

# Allow Gateway to invoke API (Backend) Cloud Run service
resource "google_cloud_run_v2_service_iam_member" "gateway_invokes_api" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_run_gateway.email}"
}

# =============================================================================
# IAM — API service account
# =============================================================================

# Allow API to invoke AI Processing Cloud Run service
resource "google_cloud_run_v2_service_iam_member" "api_invokes_ai" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ai.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_run_api.email}"
}

# =============================================================================
# IAM — API service account (per-secret access + Cloud SQL)
# =============================================================================

resource "google_secret_manager_secret_iam_member" "api_reads_jwt_secret" {
  secret_id = google_secret_manager_secret.app_secrets["jwt_secret"].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_api.email}"
}

resource "google_secret_manager_secret_iam_member" "api_reads_database_url" {
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_api.email}"
}

# Cloud SQL Auth Proxy: API service account needs cloudsql.client to connect
resource "google_project_iam_member" "api_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_api.email}"
}

# =============================================================================
# IAM — AI Processing service account (per-secret access)
# =============================================================================

resource "google_secret_manager_secret_iam_member" "ai_reads_openai_key" {
  secret_id = google_secret_manager_secret.app_secrets["openai_api_key"].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_ai.email}"
}

# =============================================================================
# IAM — GitHub Actions service account
# =============================================================================

# Push Docker images to Artifact Registry (scoped to specific repository)
resource "google_artifact_registry_repository_iam_member" "gh_actions_artifact_writer" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.images.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.github_actions.email}"
}

# Deploy to Cloud Run (per-service binding)
resource "google_cloud_run_v2_service_iam_member" "gh_actions_deploy_gateway" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.gateway.name
  role     = "roles/run.developer"
  member   = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_cloud_run_v2_service_iam_member" "gh_actions_deploy_api" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.developer"
  member   = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_cloud_run_v2_service_iam_member" "gh_actions_deploy_ai" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ai.name
  role     = "roles/run.developer"
  member   = "serviceAccount:${google_service_account.github_actions.email}"
}

# Act as Cloud Run service accounts (required for deployment)
resource "google_service_account_iam_member" "gh_actions_act_as_api_sa" {
  service_account_id = google_service_account.cloud_run_api.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_service_account_iam_member" "gh_actions_act_as_ai_sa" {
  service_account_id = google_service_account.cloud_run_ai.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_service_account_iam_member" "gh_actions_act_as_gateway_sa" {
  service_account_id = google_service_account.cloud_run_gateway.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

# Deploy to Firebase Hosting
resource "google_project_iam_member" "gh_actions_firebase_admin" {
  project = var.project_id
  role    = "roles/firebasehosting.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# =============================================================================
# Workload Identity Federation — GitHub Actions OIDC (keyless auth)
# =============================================================================

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "${var.app_name}-github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Keyless auth for GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == 'nakamu12/lumineer'"
}

resource "google_service_account_iam_member" "gh_actions_workload_identity" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/nakamu12/lumineer"
}

# =============================================================================
# Outputs for GitHub Actions secrets
# =============================================================================

output "workload_identity_provider" {
  description = "Workload Identity Provider resource name — set as GH Secret WIF_PROVIDER"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "github_actions_service_account" {
  description = "GitHub Actions SA email — set as GH Secret WIF_SERVICE_ACCOUNT"
  value       = google_service_account.github_actions.email
}
