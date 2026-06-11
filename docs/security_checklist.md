# LeadForge AI Security Checklist

## Secrets

- Replace `SECRET_KEY`, database passwords, Redis credentials, and provider tokens before production.
- Store secrets in the deployment platform secret manager.
- Never commit `.env`.

## Authentication

- Use short access-token lifetimes in production.
- Keep refresh-token rotation enabled.
- Revoke refresh tokens on logout and suspected compromise.
- Require HTTPS for all browser traffic.

## Authorization

- Use V3 roles consistently:
  - `ADMIN`: platform administration.
  - `MANAGER`: analytics, copilot, team oversight, knowledge-base management.
  - `AGENT`: lead work, memory updates, follow-up generation.
- Preserve legacy role mappings until all seeded/demo users are migrated.
- Add route-level permission tests for new high-risk endpoints.

## API Hardening

- Keep Redis rate limiting enabled.
- Restrict `CORS_ORIGINS` to production domains.
- Keep request IDs in logs and API error responses.
- Do not expose `/debug/status` publicly in production ingress rules.

## Data

- Treat lead notes, call transcripts, customer memory, and knowledge documents as sensitive customer data.
- Encrypt managed databases and backups.
- Apply retention policies to uploads, call recordings, transcripts, reports, and audit logs.
- Review knowledge-base uploads for PII and internal-only policy material.

## Infrastructure

- Run Postgres and Redis on private networks.
- Use least-privilege service accounts.
- Scan Docker images before deployment.
- Keep dependency update and vulnerability review cadence.
