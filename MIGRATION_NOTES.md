# Migration Notes: AI_Sales_Acquisition_System

Generated on: 2026-05-26 19:58:16 +05:30

## Project Type

FastAPI, Streamlit, Docker, ML/data

## Ignored Heavy/Generated Folders

.venv, venv, __pycache__, .pytest_cache, node_modules, dist, build

## Python Environment

- Install dependencies with: `python -m pip install -r requirements.txt`
- `.env.example` status: existing
- Real secret values must be restored manually from your private password manager or secure notes.

## Run Commands To Try

- `uvicorn main:app --reload`
- `uvicorn app.main:app --reload`
- `streamlit run ......python\AI_Sales_Acquisition_System\streamlit_app\app.py`
- `python backend\app\main.py`

## Laptop Restore Steps

1. Clone the GitHub repository on the new laptop.
2. Create a fresh virtual environment: `python -m venv .venv`
3. Activate it: `.\.venv\Scripts\Activate.ps1`
4. Install dependencies: `python -m pip install -r requirements.txt`
5. Create `.env` from `.env.example` and manually fill real values.
6. Run the project using one of the commands above.
