# Cloud Deployment Targets

## AWS

Use `deployment/terraform` to provision the baseline ECS-adjacent foundation, managed Postgres, and Redis. Store `SECRET_KEY`, `OPENAI_API_KEY`, and Twilio credentials in AWS Secrets Manager or SSM Parameter Store.

## Render

Use `deployment/render.yaml`. Configure production secrets in Render environment variables and attach managed Postgres/Redis.

## Railway

Use `deployment/railway.json` for backend deployment. Add separate Railway services for frontend, Postgres, Redis, and Streamlit.

## Azure

Recommended services:

- Azure Container Apps for backend, frontend, Streamlit, Prometheus, and Grafana.
- Azure Database for PostgreSQL Flexible Server.
- Azure Cache for Redis.
- Azure Key Vault for secrets.
- Application Gateway or Azure Front Door for TLS and routing.

## GCP

Recommended services:

- Cloud Run for backend, frontend, and Streamlit containers.
- Cloud SQL for PostgreSQL.
- Memorystore for Redis.
- Secret Manager for credentials.
- Cloud Load Balancing with managed certificates.

## DigitalOcean

Recommended services:

- App Platform for backend, frontend, and Streamlit.
- Managed PostgreSQL.
- Managed Redis.
- Container Registry for images.
- App Platform certificates or Cloudflare for SSL.
