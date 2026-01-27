resource "google_storage_bucket" "data_lake" {
  name          = "${var.project_id}-data-lake"
  location      = "US"
  force_destroy = true
  uniform_bucket_level_access = true
}

resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = "${var.region}-a"
  deletion_protection = false
  remove_default_node_pool = true
  initial_node_count       = 1
}

resource "google_container_node_pool" "spot_nodes" {
  name       = "spot-node-pool"
  location   = "${var.region}-a"
  cluster    = google_container_cluster.primary.name
  node_count = 1
  node_config {
    spot         = true
    machine_type = "e2-medium"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}
