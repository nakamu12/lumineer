# =============================================================================
# Firebase Hosting — Frontend (React SPA)
#
# PREREQUISITE (one-time manual step before terraform apply):
#   1. GCP コンソールで Firebase を有効化:
#      https://console.firebase.google.com/ → プロジェクトを追加 → 既存の GCP プロジェクトを選択
#   2. 完了後に terraform apply を実行
#
# Terraform manages the hosting site configuration only.
# =============================================================================

resource "google_firebase_hosting_site" "frontend" {
  provider = google-beta
  project  = var.project_id
  site_id  = "${var.app_name}-frontend"

  depends_on = [time_sleep.api_propagation]
}

# =============================================================================
# Output — Firebase Hosting URL
# =============================================================================

output "firebase_hosting_url" {
  description = "Firebase Hosting URL for the frontend"
  value       = "https://${google_firebase_hosting_site.frontend.site_id}.web.app"
}
