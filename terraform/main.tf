terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "app_network" {
  name   = "app-network-tf"
  driver = "bridge"
}

resource "docker_image" "postgres" {
  name = "postgres:15"
}

resource "docker_container" "postgres" {
  name    = "postgres_db_tf"
  image   = docker_image.postgres.name
  restart = "unless-stopped"

  env = [
    "POSTGRES_DB=sneakstore",
    "POSTGRES_USER=postgres",
    "POSTGRES_PASSWORD=postgres"
  ]

  ports {
    internal = 5432
    external = 5433
  }

  volumes {
    host_path      = abspath("${path.module}/../db/init.sql")
    container_path = "/docker-entrypoint-initdb.d/init.sql"
  }

  networks_advanced {
    name = docker_network.app_network.name
  }
}

resource "docker_image" "product_service" {
  name = "sre3-product-service-tf"
  build {
    context = abspath("${path.module}/../product_service")
    tag     = ["sre3-product-service-tf:latest"]
  }
}

resource "docker_container" "product_service" {
  name    = "product_service_tf"
  image   = docker_image.product_service.name
  restart = "unless-stopped"

  ports {
    internal = 5000
    external = 8080
  }

  env = [
    "DB_HOST=host.docker.internal",
    "DB_NAME=sneakstore",
    "DB_USER=postgres",
    "DB_PASSWORD=postgres"
  ]

  networks_advanced {
    name = docker_network.app_network.name
  }
}

resource "docker_image" "auth_service" {
  name = "sre3-auth-service-tf"
  build {
    context = abspath("${path.module}/../auth_service")
    tag     = ["sre3-auth-service-tf:latest"]
  }
}

resource "docker_container" "auth_service" {
  name    = "auth_service_tf"
  image   = docker_image.auth_service.name
  restart = "unless-stopped"

  ports {
    internal = 5000
    external = 5001
  }

  networks_advanced {
    name = docker_network.app_network.name
  }
}

resource "docker_image" "order_service" {
  name = "sre3-order-service-tf"
  build {
    context = abspath("${path.module}/../order_service")
    tag     = ["sre3-order-service-tf:latest"]
  }
}

resource "docker_container" "order_service" {
  name    = "order_service_tf"
  image   = docker_image.order_service.name
  restart = "unless-stopped"

  ports {
    internal = 5000
    external = 5003
  }

  env = [
    "DB_HOST=host.docker.internal",
    "DB_NAME=sneakstore",
    "DB_USER=postgres",
    "DB_PASSWORD=postgres"
  ]

  networks_advanced {
    name = docker_network.app_network.name
  }
}

resource "docker_image" "user_service" {
  name = "sre3-user-service-tf"
  build {
    context = abspath("${path.module}/../user_service")
    tag     = ["sre3-user-service-tf:latest"]
  }
}

resource "docker_container" "user_service" {
  name    = "user_service_tf"
  image   = docker_image.user_service.name
  restart = "unless-stopped"

  ports {
    internal = 5000
    external = 5004
  }

  networks_advanced {
    name = docker_network.app_network.name
  }
}

# Inventory Service
resource "docker_image" "inventory_service" {
  name = "sre3-inventory-service-tf"
  build {
    context = abspath("${path.module}/../inventory_service")
    tag     = ["sre3-inventory-service-tf:latest"]
  }
}

resource "docker_container" "inventory_service" {
  name    = "inventory_service_tf"
  image   = docker_image.inventory_service.name
  restart = "unless-stopped"

  ports {
    internal = 5000
    external = 5006
  }

  networks_advanced {
    name = docker_network.app_network.name
  }
}


# Recommendation Service
resource "docker_image" "recommendation_service" {
  name = "sre3-recommendation-service-tf"
  build {
    context = abspath("${path.module}/../recommendation_service")
    tag     = ["sre3-recommendation-service-tf:latest"]
  }
}

resource "docker_container" "recommendation_service" {
  name    = "recommendation_service_tf"
  image   = docker_image.recommendation_service.name
  restart = "unless-stopped"

  ports {
    internal = 5000
    external = 5007
  }

  networks_advanced {
    name = docker_network.app_network.name
  }
}

resource "docker_image" "prometheus" {
  name = "prom/prometheus:latest"
}

resource "docker_container" "prometheus" {
  name    = "prometheus_tf"
  image   = docker_image.prometheus.name
  restart = "unless-stopped"

  ports {
    internal = 9090
    external = 9090
  }

  volumes {
    host_path      = abspath("${path.module}/../prometheus.yml")
    container_path = "/etc/prometheus/prometheus.yml"
  }

  volumes {
    host_path      = abspath("${path.module}/../alert.rules.yml")
    container_path = "/etc/prometheus/alert.rules.yml"
  }

  networks_advanced {
    name = docker_network.app_network.name
  }

  command = [
    "--config.file=/etc/prometheus/prometheus.yml",
    "--storage.tsdb.path=/prometheus"
  ]
}

resource "docker_image" "grafana" {
  name = "grafana/grafana:latest"
}

resource "docker_container" "grafana" {
  name    = "grafana_tf"
  image   = docker_image.grafana.name
  restart = "unless-stopped"

  ports {
    internal = 3000
    external = 3000
  }

  env = [
    "GF_SECURITY_ADMIN_PASSWORD=admin"
  ]

  networks_advanced {
    name = docker_network.app_network.name
  }
}

resource "docker_image" "postgres_exporter" {
  name = "prometheuscommunity/postgres-exporter:latest"
}

resource "docker_container" "postgres_exporter" {
  name    = "postgres_exporter_tf"
  image   = docker_image.postgres_exporter.name
  restart = "unless-stopped"

  ports {
    internal = 9187
    external = 9187
  }

  env = [
    "DATA_SOURCE_NAME=postgresql://postgres:postgres@host.docker.internal:5433/sneakstore?sslmode=disable"
  ]

  networks_advanced {
    name = docker_network.app_network.name
  }
}