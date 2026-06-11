# LeadForge AI Architecture Audit

## Executive Summary

This repository is a full-stack AI sales platform with a FastAPI backend, Next.js frontend, Streamlit operations app, Celery workers, SQLAlchemy persistence, Redis-backed infrastructure, Docker Compose orchestration, Prometheus metrics, and ML/RAG service modules. The codebase already includes several production-oriented foundations: JWT auth with refresh tokens, RBAC helpers, audit log persistence, lead scoring, call intelligence, vector embeddings, manager copilot logic, health/readiness endpoints, Docker health checks, and CI workflows.

The upgrade should preserve existing product behavior while standardizing the platform as LeadForge AI. The safest path is incremental extension: keep legacy roles and endpoints working, add enterprise aliases and permission helpers, add missing domain models for customer memory and knowledge documents, expose new API surfaces, improve middleware and observability, and expand deployment documentation.

## Current Architecture

### Backend

- Framework: FastAPI under `backend/app`.
- Persistence: SQLAlchemy 2.x models with SQLite defaults and Postgres-compatible deployment settings.
- Schema bootstrap: `backend/app/db/migrations.py` uses `Base.metadata.create_all()` plus additive compatibility migrations.
- Auth: JWT access tokens, opaque refresh tokens stored hashed in `refresh_tokens`, and logout revocation.
- Authorization: role checks via `require_roles`, currently based on legacy enum values.
- Observability: structured JSON logs through `structlog`, in-memory Prometheus-style counters, health/readiness checks for database and Redis.
- AI services: lead scoring, RAG retrieval, embeddings, manager copilot, call intelligence, speech, WhatsApp, Twilio, and reporting services.
- Background jobs: Celery app and workers for AI/report/MLOps/notification workflows.

### Frontend

- Framework: Next.js app router under `frontend/app`.
- Styling: Tailwind CSS with local UI primitives.
- API client: `frontend/lib/api.ts` adds bearer tokens and retries once with refresh token.
- Current views: dashboard, login/register, leads, calls, analytics, reports, publishers, settings, admin panel, telecallers, counsellors, and AI insights.

### Deployment

- Local stack: `docker-compose.yml` with Postgres/pgvector, Redis, backend, workers, frontend, Nginx, Streamlit, Prometheus, and Grafana.
- Backend image includes a Docker health check against `/ready`.
- Existing deployment descriptors for Render, Railway, Terraform, Nginx, Prometheus, and GitHub Actions.

## Strengths

- Clear separation of backend routers, services, models, schemas, and workers.
- Existing compatibility-first migration strategy reduces risk for local/demo databases.
- Refresh-token storage is server-side and hashed.
- AI features have deterministic fallbacks, which keeps tests and offline demos reliable.
- Docker Compose already models production dependencies and health checks.
- Frontend API client already handles access-token refresh.

## Gaps Against LeadForge AI Requirements

### Phase 1

- Structured logging exists, but request IDs are not bound consistently.
- Global exception handling logs failures but returns framework-default error bodies.
- Rate limiting is in-memory only; Redis is configured but not used for API rate limits.
- Health, readiness, metrics, and Docker health checks are present and should be retained.

### Phase 2

- RBAC exists but uses legacy roles. V3 requires ADMIN, MANAGER, AGENT semantics.
- Refresh token flow exists but does not rotate tokens on refresh.
- Audit logs exist but need broader write coverage and query APIs.
- Permission enforcement is uneven across routers.

### Phase 3

- Lead fields and call analysis store some memory-like data, but there is no dedicated customer memory model/API.

### Phase 4

- Lead score, explanation, sentiment score field, and next best action exist.
- Intent classification, objection detection, and sentiment analysis need a consolidated API facade.

### Phase 5

- Messaging integrations exist, but a direct follow-up generation API for WhatsApp, email, and call scripts is missing.

### Phase 6

- Vector embeddings and RAG service exist with JSON-vector fallback.
- Dedicated document upload, search, and ask-with-citations endpoints are missing.

### Phase 7

- Manager copilot service exists but needs explicit endpoints for best agents, hot leads, followups due, objection analytics, and conversion analytics.

### Phase 8

- Dashboard exists but does not yet surface V3 modules: hot leads, conversion rate, AI insights, customer memory, knowledge base, manager copilot, and follow-up generation.

### Phase 9

- CI exists, but should explicitly validate backend tests, frontend build, and Docker images.

### Phase 10

- Production Compose and security checklist need to be added or expanded.

## Compatibility Risks

- Replacing role enum values would break seeded demo users and existing tests. V3 roles should be mapped onto existing values instead.
- Changing auth response shapes would break frontend login and refresh logic. New fields should be additive.
- Replacing existing RAG storage with pgvector-only storage would break SQLite/dev mode. Keep JSON-vector fallback and use pgvector opportunistically.
- Reworking dashboard routes could break current frontend pages. Add new analytics fields and routes while keeping current response keys.

## Recommended V3 Implementation Strategy

1. Keep all existing endpoints and models.
2. Add request ID middleware, global exception handlers, and Redis-first rate limiting with in-memory fallback.
3. Add V3 permission helpers that map ADMIN to `super_admin`, MANAGER to `manager`, and AGENT to `telecaller`/`counsellor`.
4. Add customer memory and knowledge document models with additive migrations.
5. Add API routers for memory, lead intelligence, follow-ups, knowledge base, manager copilot, and audit logs.
6. Extend frontend dashboard and API client surfaces without deleting existing pages.
7. Add production Compose, deployment documentation, security checklist, CI hardening, and focused tests.
