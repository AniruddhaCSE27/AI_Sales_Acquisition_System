# API Documentation

Interactive Swagger docs are available at `/api/v1/openapi.json` and `/docs` when the backend runs.

Core groups:

- `/auth`: register and login.
- `/leads`: CRUD, CSV upload, filtering, lead prioritization.
- `/calls`: click-to-call, transcript analysis, Twilio webhooks.
- `/analytics`: dashboards, funnel, leaderboard.
- `/ai`: manager chat and lead recommendations.
- `/publishers`: publisher quality and ROI analytics.
- `/reports`: weekly AI PDF generation.
- `/ws/telecaller-assistant/{lead_id}`: live guidance WebSocket.

