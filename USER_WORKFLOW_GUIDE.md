# LeadForage AI User Workflow Guide

## Sign In

Open `http://localhost:3000`.

Unauthenticated users are redirected to `/login`.

Bootstrap admin:

- Email: `admin@demo.com`
- Password: `Password123!`

## Lead Workflow

Recommended operating flow:

1. Publisher uploads CSV/XLSX/Merrito export.
2. LeadForage maps fields and imports clean leads.
3. AI scoring labels each lead Hot, Warm, or Cold.
4. Manager assigns Hot/Warm leads to telecallers.
5. Telecaller calls leads and captures notes/outcomes.
6. Objections and sentiment update the next action.
7. Interested leads are assigned to counsellors.
8. Counsellors update outcome as Converted or Rejected.
9. Manager reviews analytics, RAG insights, and weekly reports.

## Add A Lead

Go to `/leads` and enter:

- name
- phone
- email
- course
- source
- city
- budget
- lead notes
- publisher
- tags

The lead is saved to PostgreSQL and scored immediately.

## Bulk Import

Go to `/leads`, choose a CSV/XLSX file, preview detected field mapping, then import.

For Merrito exports, use the Merrito import button. The importer detects common Merrito fields:

- name
- phone
- email
- course
- campaign
- source
- publisher
- status

The system records import history, errors, and duplicate reports.

## Duplicate Handling

Duplicates are blocked by:

- phone
- email
- fuzzy name match

Duplicate API responses return `409`.

## Manager AI Copilot

Use the manager RAG endpoint to ask questions such as:

- Why are conversions down?
- Which publisher gives best leads?
- Which leads should be called today?
- What objections are common this week?

The answer is retrieved from CRM records, lead notes, transcripts, and reports.

## Reports

Use weekly report generation to create a PDF and AI manager summary from current CRM data.

## Operations

Monitor:

- `/ready`
- `/metrics`
- Docker service health
- `/api/v1/operations/jobs`
- Prometheus
- Grafana
