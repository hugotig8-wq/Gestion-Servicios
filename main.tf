provider "google" {
  project = "TU_PROJECT_ID"
  region  = "us-central1"
}

# Máquina virtual gratuita para Postgres y Next.js
resource "google_compute_instance" "vm_free_tier" {
  name         = "instancia-desarrollo"
  machine_type = "e2-micro" # Nivel gratuito
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral IP para acceder vía web
    }
  }
}
