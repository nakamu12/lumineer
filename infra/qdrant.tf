# =============================================================================
# GCE — Qdrant Vector Database (e2-micro)
#
# Runs Qdrant in a Docker container on a minimal GCE instance.
# Data: public Coursera course embeddings (~80MB), read-heavy workload.
# =============================================================================

# Enable Compute Engine API
resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

# =============================================================================
# Static external IP (stable across instance restarts)
# =============================================================================

locals {
  # Derive region from zone (e.g., "asia-northeast2-a" → "asia-northeast2")
  qdrant_region = join("-", slice(split("-", var.qdrant_zone), 0, 2))
}

resource "google_compute_address" "qdrant" {
  name   = "${var.app_name}-qdrant-ip"
  region = local.qdrant_region

  depends_on = [google_project_service.compute]
}

# =============================================================================
# Service Account (minimal permissions)
# =============================================================================

resource "google_service_account" "qdrant" {
  account_id   = "${var.app_name}-qdrant-sa"
  display_name = "Lumineer Qdrant GCE SA"
  description  = "Service account for GCE Qdrant instance (minimal permissions)"
}

# =============================================================================
# GCE Instance — e2-micro with Qdrant container
# =============================================================================

resource "google_compute_instance" "qdrant" {
  name         = "${var.app_name}-qdrant"
  machine_type = var.qdrant_machine_type
  zone         = var.qdrant_zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = var.qdrant_disk_size_gb
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.qdrant.address
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e

    # Skip if Qdrant is already running
    if docker ps --format '{{.Names}}' | grep -q qdrant; then
      echo "Qdrant already running, skipping setup"
      exit 0
    fi

    # Install Docker
    apt-get update
    apt-get install -y docker.io
    systemctl enable docker
    systemctl start docker

    # Create persistent data directory
    mkdir -p /var/lib/qdrant/storage

    # Run Qdrant (no API key — firewall-protected, public course data)
    docker run -d --restart=always \
      --name qdrant \
      -p 6333:6333 \
      -v /var/lib/qdrant/storage:/qdrant/storage \
      qdrant/qdrant:v1.13.2
  EOF

  tags = ["qdrant"]

  service_account {
    email = google_service_account.qdrant.email
    # Minimal scopes — Qdrant container needs no GCP API access
    scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring.write",
    ]
  }

  # Allow Terraform to stop the instance for updates
  allow_stopping_for_update = true

  depends_on = [google_project_service.compute]
}

# =============================================================================
# Firewall — allow Qdrant HTTP API (port 6333)
# =============================================================================

resource "google_compute_firewall" "qdrant" {
  name    = "${var.app_name}-allow-qdrant"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["6333"]
  }

  # Cloud Run uses shared egress IPs that can't be pinned.
  # Qdrant serves public Coursera data only — no sensitive data.
  # For tighter security, add API key auth later.
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["qdrant"]

  depends_on = [google_project_service.compute]
}
