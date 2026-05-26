# LeadForage AI MLOps Report

Date: 2026-05-24

## Model Training

New training entry point:

- `ai_models/train_lead_conversion.py`

The trainer attempts:

1. LightGBM
2. XGBoost
3. Logistic Regression baseline

Validated local training produced:

- Model type: Logistic Regression
- Accuracy: `0.65`
- ROC AUC: `0.7508`
- Training rows: `240` synthetic bootstrap rows

## Model Registry

New registry helper:

- `ai_models/model_registry.py`

Registry outputs:

- Versioned manifest JSON
- Active manifest pointer
- Serialized model artifact
- Metrics
- Feature order

Current active files:

- `ai_models/registry/lead_conversion_active.json`
- `ai_models/registry/lead_conversion_logistic_regression.joblib`

## Feature Set

Lead conversion features:

- source
- publisher
- course
- city
- budget
- lead age
- call attempts
- response status
- follow-up count
- WhatsApp response
- counsellor outcome
- engagement score

## Explainability

Current explainability:

- Model-backed feature importance or coefficients when available
- Deterministic fallback factor contribution when no trained model is available

SHAP is listed as a production dependency and can be enabled against trained tree models once real historical data is available.

## Async MLOps

Celery task:

- `retrain_lead_model`

Queue:

- `mlops`

Tracking:

- `ai_jobs`
- `model_training_runs`
- `model_registry`

## Recommended Next Steps

- Backfill real historical lead outcomes.
- Add scheduled weekly retraining after enough labeled conversions exist.
- Promote model only if ROC AUC, calibration, and conversion lift exceed baseline.
- Add drift monitoring by source, publisher, city, and course.
