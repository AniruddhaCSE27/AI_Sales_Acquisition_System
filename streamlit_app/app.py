import json
import os
import subprocess
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="LeadForge AI", layout="wide")
st.title("LeadForge AI")
st.caption("Forge conversations into conversions with autonomous sales intelligence.")


def get_json(path: str):
    response = requests.get(f"{BACKEND_URL}{path}", timeout=5)
    response.raise_for_status()
    return response.json()


def login():
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"email": "admin@demo.com", "password": "Password123!"},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def auth_headers():
    if "token" not in st.session_state:
        st.session_state["token"] = login()
    return {"Authorization": f"Bearer {st.session_state['token']}"}


health_col, action_col = st.columns([2, 1])
with health_col:
    st.subheader("Platform Health")
    try:
        health = get_json("/debug/status")
        deps = [{"dependency": name, **value} for name, value in health["dependencies"].items()]
        st.dataframe(pd.DataFrame(deps), use_container_width=True)
    except Exception as exc:
        st.error(f"Health unavailable: {exc}")

with action_col:
    st.subheader("Operations")
    if st.button("Seed DB", use_container_width=True):
        response = requests.post(f"{BACKEND_URL}/api/v1/operations/seed", headers=auth_headers(), timeout=10)
        st.write(response.json())
    if st.button("Generate Report", use_container_width=True):
        response = requests.post(f"{BACKEND_URL}/api/v1/reports/weekly", headers=auth_headers(), timeout=20)
        st.write(response.json())
    if st.button("Retrain", use_container_width=True):
        result = subprocess.run(["python", "ai_models/retrain_pipeline.py"], cwd="/workspace", capture_output=True, text=True, timeout=120)
        st.code(result.stdout or result.stderr)

st.subheader("Analytics")
try:
    dashboard = requests.get(f"{BACKEND_URL}/api/v1/analytics/dashboard", headers=auth_headers(), timeout=5).json()
    kpis = dashboard["kpis"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leads", kpis["total_leads"])
    c2.metric("Converted", kpis["converted_leads"])
    c3.metric("Conversion", f"{kpis['conversion_rate']}%")
    c4.metric("Revenue", kpis["predicted_revenue"])
    source_df = pd.DataFrame(dashboard["lead_sources"])
    if not source_df.empty:
        st.plotly_chart(px.bar(source_df, x="source", y="leads", color="avg_probability"), use_container_width=True)
        st.download_button("Export CSV", source_df.to_csv(index=False), "lead_sources.csv", "text/csv")
except Exception as exc:
    st.warning(f"Analytics unavailable: {exc}")

st.subheader("Manager Chat")
question = st.text_input("Ask a manager question", value="Why are conversions down?")
if st.button("Ask Manager Copilot"):
    response = requests.post(f"{BACKEND_URL}/api/v1/ai/manager-copilot", headers=auth_headers(), json={"question": question}, timeout=10)
    st.write(response.json())

st.subheader("Model Registry")
try:
    registry = requests.get(f"{BACKEND_URL}/api/v1/operations/model-registry", headers=auth_headers(), timeout=5).json()
    st.dataframe(pd.DataFrame(registry), use_container_width=True)
except Exception as exc:
    st.info(f"No model registry entries yet: {exc}")

st.subheader("Recent Logs")
log_dir = Path("/workspace/logs")
if log_dir.exists():
    for path in sorted(log_dir.glob("*.log"))[-3:]:
        st.caption(path.name)
        st.code(path.read_text(encoding="utf-8", errors="ignore")[-4000:])
else:
    st.info("No log files found.")

st.subheader("Pipeline Status")
st.json({"twilio_streaming": "enabled", "whisper": "enabled", "objection_detection": "enabled", "model_registry": "enabled"})
st.divider()
st.caption("LeadForge AI - Forge conversations into conversions with autonomous sales intelligence.")
