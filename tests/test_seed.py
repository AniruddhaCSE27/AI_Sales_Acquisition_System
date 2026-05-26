from app.db.session import SessionLocal
from app.models import Lead, PerformanceMetric, Publisher, Report, Role, User
from app.seed import run_seed


def test_seed_is_idempotent():
    with SessionLocal() as db:
        first = run_seed(db)
        second = run_seed(db)

        assert db.query(User).filter(User.email == "admin@demo.com", User.role == Role.super_admin).count() == 1
        assert db.query(User).filter(User.email != "admin@demo.com").count() == 0
        assert db.query(Publisher).count() == 0
        assert db.query(Lead).count() == 0
        assert db.query(PerformanceMetric).count() == 0
        assert db.query(Report).count() == 0
        assert first["users"] >= 0
        assert second["users"] == 0
