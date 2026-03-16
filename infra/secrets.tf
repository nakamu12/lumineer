# =============================================================================
# Secret Manager — application secrets
# Secret values are NOT set by Terraform (set manually or via CI/CD)
# Terraform only creates the secret resource (the "slot").
# =============================================================================

locals {
  secrets = {
    openai_api_key  = "OpenAI API key for LLM and Embedding calls"
    qdrant_url      = "Qdrant Cloud cluster URL"
    qdrant_api_key  = "Qdrant Cloud API key"
  }
}

resource "google_secret_manager_secret" "app_secrets" {
  for_each  = local.secrets
  secret_id = "${var.app_name}-${replace(each.key, "_", "-")}"

  replication {
    auto {}
  }

  labels = {
    app = var.app_name
    env = var.environment
  }

  depends_on = [time_sleep.api_propagation]
}

# =============================================================================
# Outputs — secret resource names for manual value injection
# After terraform apply, set values with:
#   gcloud secrets versions add lumineer-openai-api-key --data-file=<(echo -n "sk-...")
# =============================================================================

output "secret_names" {
  description = "Secret Manager resource names — set values manually after apply"
  value       = { for k, v in google_secret_manager_secret.app_secrets : k => v.name }
}
