# =============================================================================
# Outputs — values needed after terraform apply
# =============================================================================

output "gateway_service_url" {
  description = "Cloud Run URL for the Gateway (Hono) service — public entry point"
  value       = google_cloud_run_v2_service.gateway.uri
}

output "api_service_url" {
  description = "Cloud Run URL for the API (Hono) service"
  value       = google_cloud_run_v2_service.api.uri
}

output "ai_service_url" {
  description = "Cloud Run URL for the AI Processing (Python) service"
  value       = google_cloud_run_v2_service.ai.uri
}

output "gateway_service_account_email" {
  description = "Service account email used by Cloud Run Gateway service"
  value       = google_service_account.cloud_run_gateway.email
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

output "qdrant_external_ip" {
  description = "Qdrant GCE instance external IP"
  value       = google_compute_address.qdrant.address
}

output "qdrant_url" {
  description = "Qdrant HTTP API URL for AI Processing service"
  value       = "http://${google_compute_address.qdrant.address}:6333"
}
