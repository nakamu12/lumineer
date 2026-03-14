# =============================================================================
# Required variables — set in terraform.tfvars (never commit)
# =============================================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run services"
  type        = string
  default     = "asia-northeast1" # Tokyo
}

# =============================================================================
# App settings
# =============================================================================

variable "app_name" {
  description = "Application name prefix for all resources"
  type        = string
  default     = "lumineer"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be 'dev' or 'prod'."
  }
}

# =============================================================================
# Cloud Run — API (Hono)
# =============================================================================

variable "api_image" {
  description = "Docker image for API (Hono) service. e.g. gcr.io/<project>/lumineer-api:latest"
  type        = string
}

variable "api_min_instances" {
  description = "Minimum number of API instances (0 for cost savings, 1 for demo warm-up)"
  type        = number
  default     = 0
}

variable "api_max_instances" {
  description = "Maximum number of API instances"
  type        = number
  default     = 3
}

variable "api_memory" {
  description = "Memory limit for API instances"
  type        = string
  default     = "512Mi"
}

variable "api_cpu" {
  description = "CPU limit for API instances"
  type        = string
  default     = "1"
}

# =============================================================================
# Cloud Run — AI Processing (Python)
# =============================================================================

variable "ai_image" {
  description = "Docker image for AI Processing (Python) service"
  type        = string
}

variable "ai_min_instances" {
  description = "Minimum number of AI Processing instances"
  type        = number
  default     = 0
}

variable "ai_max_instances" {
  description = "Maximum number of AI Processing instances"
  type        = number
  default     = 2
}

variable "ai_memory" {
  description = "Memory limit for AI Processing instances (needs more for ML libs)"
  type        = string
  default     = "2Gi"
}

variable "ai_cpu" {
  description = "CPU limit for AI Processing instances"
  type        = string
  default     = "2"
}

# =============================================================================
# Firebase
# =============================================================================

variable "firebase_location" {
  description = "Firebase Hosting default location"
  type        = string
  default     = "asia-east1"
}
