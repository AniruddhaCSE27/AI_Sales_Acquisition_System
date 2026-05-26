# LeadForage AI Test Report

Date: 2026-05-24

## Automated Tests

Command:

```powershell
$env:DATABASE_URL='sqlite:///C:/Users/ANIRUDDHA PATHAK/Documents/Codex/2026-05-24/you-are-a-principal-ai-engineer/test_sales_ai_phase4.db'
C:\Users\ANIRUDDHA PATHAK\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest
```

Result:

- `14 passed`

Coverage added or repaired:

- Auth login/refresh tests
- Clean seed tests
- Lead CRUD smoke tests
- Duplicate detection coverage through API validation
- AI lead scoring tests
- Call intelligence tests
- RAG indexing/retrieval tests
- Report generation tests
- Twilio stream/copilot tests
- Model retraining registry tests

## Model Training Validation

Command:

```powershell
C:\Users\ANIRUDDHA PATHAK\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ai_models.train_lead_conversion
```

Result:

- Active model artifact generated
- Active manifest generated
- ROC AUC: `0.7508`

## Docker Validation

Command:

```powershell
docker compose up --build -d
```

Result:

- Full stack built and started
- Final Docker service health: all services healthy

## Manual Runtime API Validation

Validated against running Docker stack:

- frontend redirect: `307 /login?next=%2F`
- login: `200`
- clean leads before workflow: `0`
- add lead: `200`, AI score `72.5`
- duplicate create: `409`
- CSV import: `200`, created `1`, errors `0`
- Merrito import: `200`, duplicate skipped
- weekly report: `200`
- RAG manager query: `200`, sources returned
- readiness: `200 ready`
- Redis/Postgres restart recovery: login and lead list still work

## Log Review

Final backend logs after fixes show normal request completion lines and no active tracebacks.

Celery logs show expected reconnect behavior during Redis restart, then successful broker reconnection.
