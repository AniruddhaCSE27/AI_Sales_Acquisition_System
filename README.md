# LeadForage AI

Forge conversations into conversions with autonomous sales intelligence.

Production-grade AI Sales Intelligence SaaS for education sales teams. The platform combines CRM workflows, JWT/RBAC, multi-tenant data boundaries, Twilio voice streams, Whisper call intelligence, live telecaller copilot, WhatsApp automation, manager RAG, Celery workers, retraining pipelines, Streamlit operations, Docker, CI/CD, and observability.

## Architecture

- Frontend: Next.js SaaS dashboard on port `3000`
- Backend: FastAPI API on port `8000`
- Database: PostgreSQL 16 with pgvector
- Cache/queue: Redis 7 and Celery worker/beat
- Reverse proxy: Nginx on port `8080`
- Operations portal: Streamlit on port `8501`
- Metrics: Prometheus on port `9090`
- Dashboards: Grafana on port `3001`
- AI services: OpenAI GPT and Whisper with deterministic offline fallback paths
- Voice: Twilio calls and Media Streams WebSocket ingestion
- ML: LightGBM/XGBoost-preferred lead conversion scoring with Logistic Regression baseline and model registry

## Production Upgrade Reports

- `PRODUCTION_AI_UPGRADE_REPORT.md`
- `MLOPS_REPORT.md`
- `DEPLOYMENT_READY.md`
- `TEST_REPORT.md`
- `USER_WORKFLOW_GUIDE.md`

## Quick Start

```powershell
docker compose up --build -d
docker compose exec -T backend sh -c "PYTHONPATH=/app python scripts/seed.py"
```

Open:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Streamlit ops: http://localhost:8501
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

Demo login:

- Email: `admin@demo.com`
- Password: `Password123!`

## Validation

Run the full production validation:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\full_validate.ps1
```

The script builds Docker images, starts the stack, waits for health, runs migrations, seeds the database, runs backend tests, validates login, checks APIs, checks metrics, verifies Streamlit/Prometheus/Grafana, and simulates a Twilio call intelligence workflow.

## Environment Variables

Backend:

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `WHISPER_MODEL`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `TWILIO_STREAM_PATH`
- `MODEL_REGISTRY_DIR`
- `VECTOR_DB_DIR`
- `SENTRY_DSN`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `CORS_ORIGINS`

Frontend:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_WS_URL`

## Twilio Voice AI

The voice pipeline supports:

- Incoming and outgoing calls
- Twilio Media Streams WebSocket ingestion
- Call event persistence
- Reconnect/retry metadata
- Recording metadata
- Whisper transcription
- Objection detection
- CRM call and lead updates
- WhatsApp follow-up events

Primary endpoints:

- `POST /api/v1/calls/click-to-call`
- `POST /api/v1/calls/twilio/voice`
- `POST /api/v1/calls/simulate-stream/{lead_id}`
- `WS /api/v1/ws/twilio/media`
- `WS /api/v1/ws/telecaller-copilot/{lead_id}`

## Streamlit Operations Portal

The operations portal provides:

- Service and dependency health
- Model registry view
- Retraining trigger
- Seed DB button
- Generate report button
- Manager copilot chat
- Analytics charts
- CSV export
- Recent logs

## Retraining

Run manually:

```powershell
docker compose exec backend python /app/ai_models/retrain_pipeline.py
```

The pipeline trains Logistic Regression and Random Forest. XGBoost is used when optional ML dependencies are installed from `backend/requirements-ml.txt`. Artifacts and manifest files are written to the model registry directory.

## Observability

Backend exposes Prometheus metrics at:

```text
GET /metrics
```

Tracked signals:

- API request count
- API latency
- AI latency
- Call failures
- Service uptime
- Dependency health

Grafana runs on `http://localhost:3001` with default local credentials `admin/admin`.

## Cloud Deployment

Deployment assets live in `deployment/`:

- `deployment/render.yaml`
- `deployment/railway.json`
- `deployment/terraform`
- `deployment/nginx.production.conf`
- `deployment/cloud-targets.md`

Supported deployment paths include AWS, Render, Railway, Azure, GCP, and DigitalOcean.

## GitHub Actions

Workflows:

- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`

CI runs backend tests, frontend Docker build, Docker validation, and filesystem security scanning.

## Production Checklist

- Replace demo credentials and `SECRET_KEY`
- Store all secrets in a real secret manager
- Configure Twilio webhook URLs and Media Stream URL
- Configure OpenAI credentials and spending limits
- Enable managed Postgres backups
- Add Alembic revisioned migrations before multi-region production
- Configure Sentry/OpenTelemetry exporters
- Put Nginx behind TLS with managed certificates
- Add rate limits for auth and webhook routes
- Run `scripts/full_validate.ps1` before every release
