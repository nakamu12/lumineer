# =============================================================================
# Outputs — values needed after terraform apply
# =============================================================================

output "api_service_url" {
  description = "Cloud Run URL for the API (Hono) service"
  value       = google_cloud_run_v2_service.api.uri
}

output "ai_service_url" {
  description = "Cloud Run URL for the AI Processing (Python) service"
  value       = google_cloud_run_v2_service.ai.uri
}

output "api_service_account_email" {
  description = "Service account email used by Cloud Run API service"
  value       = google_service_account.cloud_run_api.email
}

output "ai_service_account_email" {
  description = "Service account email used by Cloud Run AI service"
  value       = google_service_account.cloud_run_ai.email
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL for pushing Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}
