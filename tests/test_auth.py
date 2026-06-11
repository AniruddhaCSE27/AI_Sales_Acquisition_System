from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.seed import run_seed
from app.schemas import UserCreate
from app.models import Role


def test_admin_login_and_refresh():
    with SessionLocal() as db:
        run_seed(db)

    client = TestClient(app)
    response = client.post("/api/v1/auth/login", json={"email": "admin@demo.com", "password": "Password123!"})
    assert response.status_code == 200
    token = response.json()["access_token"]

    refresh = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {token}"})
    assert refresh.status_code == 200
    assert refresh.json()["token_type"] == "bearer"


def test_bad_login_is_rejected():
    client = TestClient(app)
    response = client.post("/api/v1/auth/login", json={"email": "admin@demo.com", "password": "wrong-password"})
    assert response.status_code == 401


def test_enterprise_role_aliases_are_accepted():
    assert UserCreate(name="Admin", email="admin-alias@example.com", password="Password123!", role="ADMIN").role == Role.admin
    assert UserCreate(name="Manager", email="manager-alias@example.com", password="Password123!", role="MANAGER").role == Role.manager
    assert UserCreate(name="Agent", email="agent-alias@example.com", password="Password123!", role="AGENT").role == Role.agent
