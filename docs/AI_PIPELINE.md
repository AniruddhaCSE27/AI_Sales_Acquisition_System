# AI Pipeline

1. Leads are scored immediately on creation using deterministic fallback rules.
2. Historical datasets train Logistic Regression, Random Forest, and XGBoost models.
3. Best model metrics are stored under `ai_models/registry`.
4. Call transcripts are summarized and analyzed for sentiment, intent, objections, and next actions.
5. Manager assistant combines structured analytics with GPT-generated recommendations when `OPENAI_API_KEY` is configured.
6. Weekly reports convert analytics and AI recommendations into PDFs.

Production expansion points:

- Replace fallback scoring with model loading from a registry.
- Add vector storage for semantic call and lead search.
- Add background workers for transcription, retraining, and report delivery.
- Add human review queues for AI-sensitive decisions.

