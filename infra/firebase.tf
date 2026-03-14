# =============================================================================
# Firebase Hosting — Frontend (React SPA)
# Note: Firebase resources require the Firebase project to be initialized first.
# Run: firebase init hosting  (one-time manual step)
# Terraform manages the hosting site configuration only.
# =============================================================================

resource "google_firebase_hosting_site" "frontend" {
  provider = google-beta
  project  = var.project_id
  site_id  = "${var.app_name}-frontend"

  depends_on = [google_project_service.services]
}

# =============================================================================
# Output — Firebase Hosting URL
# =============================================================================

output "firebase_hosting_url" {
  description = "Firebase Hosting URL for the frontend"
  value       = "https://${google_firebase_hosting_site.frontend.site_id}.web.app"
}
