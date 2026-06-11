# LeadForge AI Deployment Guide

## Local Demo

Use this path first when Docker image pulls are unreliable.

```powershell
cd C:\Projects\AI_Sales_Acquisition_System
pip install -r backend\requirements.txt
$env:DATABASE_URL="sqlite:///./sales_ai.db"
$env:SEED_DEMO_DATA="true"
python scripts\seed_demo.py
```

Start the backend:

```powershell
$env:DATABASE_URL="sqlite:///./sales_ai.db"
$env:REDIS_URL="redis://localhost:6379/0"
$env:SEED_DEMO_DATA="true"
$env:REQUIRE_REDIS_FOR_READINESS="false"
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Start the frontend:

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8000/api/v1"
npm run dev
```

Demo credentials:

- Email: `admin@demo.com`
- Password: `Password123!`

## Validation Checklist

```powershell
pytest tests
cd frontend
npm run build
cd ..
docker compose config
$env:POSTGRES_PASSWORD="validation-only"
docker compose -f docker-compose.prod.yml config
```

Verify local endpoints:

```powershell
curl.exe -i http://localhost:8000/health
curl.exe -i http://localhost:8000/ready
curl.exe -i http://localhost:8000/metrics
```

## Production Compose

Create a `.env` file from `.env.example`, set real secrets, then run:

```powershell
$env:POSTGRES_PASSWORD="<strong-password>"
docker compose -f docker-compose.prod.yml up --build -d
```

Production readiness should keep `REQUIRE_REDIS_FOR_READINESS=true`.

## Known Docker Network Issue

If Docker reports CloudFront or Docker Hub `EOF` while pulling images such as `redis:7-alpine` or `pgvector/pgvector:pg16`, the application code is not the failing component. Retry on a different network or pre-pull:

```powershell
docker pull redis:7-alpine
docker pull pgvector/pgvector:pg16
docker pull nginx:1.27-alpine
docker pull prom/prometheus:v2.55.1
docker pull grafana/grafana:11.4.0
```
