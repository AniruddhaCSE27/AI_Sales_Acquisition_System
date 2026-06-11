from app.db.session import SessionLocal
from app.core.security import verify_password
from app.models import Lead, Organization, PerformanceMetric, Publisher, Report, Role, User
from app.seed import ensure_demo_admin, run_seed


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


def test_safe_demo_seed_repairs_admin_without_deleting_data():
    with SessionLocal() as db:
        org = db.query(Organization).filter(Organization.slug == "demo").first()
        if org is None:
            org = Organization(name="Demo Organization", slug="demo", primary_domain="demo.localhost")
            db.add(org)
            db.flush()
        user = db.query(User).filter(User.email == "admin@demo.com").first()
        if user is None:
            user = User(name="Broken Demo", email="admin@demo.com", hashed_password="bad-hash", role=Role.agent, is_active=False, organization_id=org.id)
            db.add(user)
        else:
            user.hashed_password = "bad-hash"
            user.role = Role.agent
            user.is_active = False
        db.commit()

        ensure_demo_admin(db)
        repaired = db.query(User).filter(User.email == "admin@demo.com").one()
        assert repaired.is_active is True
        assert repaired.role == Role.super_admin
        assert verify_password("Password123!", repaired.hashed_password)
