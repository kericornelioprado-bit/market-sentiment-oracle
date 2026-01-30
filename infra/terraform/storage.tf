# infra/terraform/storage.tf

resource "google_storage_bucket" "data_lake" {
  name          = "${var.project_id}-data-lake" # Usará tu ID de proyecto como prefijo
  location      = var.region
  storage_class = "STANDARD"
  force_destroy = true # Permite borrarlo aunque tenga archivos (útil para dev)

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = "dev"
    managed_by  = "terraform"
  }
}

output "data_lake_bucket_name" {
  value = google_storage_bucket.data_lake.name
}