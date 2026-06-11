# LeadForge AI Production Deployment

## Required Services

- Postgres 16 with pgvector preferred.
- Redis 7 for Celery, refresh workflows, and Redis-backed API rate limiting.
- FastAPI backend.
- Celery worker.
- Next.js frontend.
- Nginx or a managed ingress/proxy.

## Environment

Create `.env` from `.env.example` and replace every placeholder:

- `SECRET_KEY`: long random value.
- `DATABASE_URL`: managed Postgres URL or the Compose Postgres URL.
- `REDIS_URL`: managed Redis URL or the Compose Redis URL.
- `CORS_ORIGINS`: production frontend origins only.
- `NEXT_PUBLIC_API_URL`: public API URL ending in `/api/v1`.
- `NEXT_PUBLIC_WS_URL`: public WebSocket URL ending in `/api/v1/ws`.
- AI/voice provider keys only when those integrations are enabled.

## Docker Compose Production Run

```powershell
Copy-Item .env.example .env
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

Validate:

```powershell
curl http://localhost/health
curl http://localhost/ready
curl http://localhost/metrics
```

## Database

The app creates missing tables on boot through the existing additive schema bootstrap. For long-lived production systems, convert those additive migrations into reviewed Alembic revisions before multi-team operation.

## RAG Backend

LeadForge AI stores embeddings through the existing `vector_embeddings` table. Postgres deployments should enable pgvector. Local and restricted environments continue to use JSON-vector fallback so upload, search, and ask endpoints remain available.

## Operations

- Keep `/ready` as the container health check target.
- Monitor `/metrics` with Prometheus.
- Alert on high `api_requests_total` error rates, readiness failures, Redis downtime, and worker restarts.
- Use object storage for large uploads, generated reports, and model artifacts once data grows beyond single-node volumes.
