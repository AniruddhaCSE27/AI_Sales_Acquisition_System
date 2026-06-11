from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.migrations import ensure_schema
from app.db.session import engine
from app.models import AIJob, Activity, AuditLog, Call, CallStreamEvent, CallTranscript, CallTranscriptAnalysis, ImportBatch, Lead, Organization, OrganizationUser, PerformanceMetric, Publisher, RefreshToken, Report, Role, Subscription, SubscriptionStatus, User, VectorEmbedding

DEMO_PASSWORD = "Password123!"

DEMO_USERS = [
    ("Demo Admin", "admin@demo.com", Role.super_admin),
]


def _password_matches(password: str, hashed: str) -> bool:
    try:
        return verify_password(password, hashed)
    except Exception:
        return False


def ensure_demo_admin(db: Session) -> dict[str, int | bool]:
    """Create or repair only the local demo admin without deleting CRM data."""
    org = db.query(Organization).filter(Organization.slug == "demo").first()
    organization_created = org is None
    if org is None:
        org = Organization(name="Demo Organization", slug="demo", primary_domain="demo.localhost")
        db.add(org)
        db.flush()

    subscription = db.query(Subscription).filter(Subscription.organization_id == org.id).first()
    if subscription is None:
        db.add(Subscription(organization_id=org.id, plan="trial", status=SubscriptionStatus.active, seats=25))

    password = settings.seed_default_password or DEMO_PASSWORD
    user = db.query(User).filter(User.email == "admin@demo.com").first()
    user_created = user is None
    if user is None:
        user = User(
            name="Demo Admin",
            email="admin@demo.com",
            hashed_password=hash_password(password),
            role=Role.super_admin,
            is_active=True,
            organization_id=org.id,
        )
        db.add(user)
    else:
        user.organization_id = org.id
        user.name = "Demo Admin"
        user.role = Role.super_admin
        user.is_active = True
        if not _password_matches(password, user.hashed_password):
            user.hashed_password = hash_password(password)
    db.flush()

    membership = db.query(OrganizationUser).filter(OrganizationUser.organization_id == org.id, OrganizationUser.user_id == user.id).first()
    if membership is None:
        db.add(OrganizationUser(organization_id=org.id, user_id=user.id, role=user.role))
    else:
        membership.role = user.role
    db.commit()
    return {"user_id": user.id, "user_created": user_created, "organization_created": organization_created}


def run_seed(db: Session) -> dict[str, int]:
    ensure_schema(engine)
    counts = {"users": 0, "removed_demo_rows": 0}
    org = db.query(Organization).filter(Organization.slug == "demo").first()
    if org is None:
        org = Organization(name="Demo Organization", slug="demo", primary_domain="demo.localhost")
        db.add(org)
    db.flush()
    subscription = db.query(Subscription).filter(Subscription.organization_id == org.id).first()
    if subscription is None:
        db.add(Subscription(organization_id=org.id, plan="trial", status=SubscriptionStatus.active, seats=25))

    counts["removed_demo_rows"] += db.query(CallTranscriptAnalysis).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(CallTranscript).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(CallStreamEvent).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(Call).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(Activity).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(ImportBatch).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(VectorEmbedding).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(AIJob).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(Lead).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(PerformanceMetric).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(Report).delete(synchronize_session=False)
    counts["removed_demo_rows"] += db.query(Publisher).delete(synchronize_session=False)

    demo_user_ids = [user.id for user in db.query(User).filter(User.email.like("%@demo.com"), User.email != "admin@demo.com").all()]
    if demo_user_ids:
        for model in (RefreshToken, AuditLog):
            counts["removed_demo_rows"] += db.query(model).filter(model.user_id.in_(demo_user_ids)).delete(synchronize_session=False)
        db.query(OrganizationUser).filter(OrganizationUser.user_id.in_(demo_user_ids)).delete(synchronize_session=False)
        counts["removed_demo_rows"] += db.query(User).filter(User.id.in_(demo_user_ids)).delete(synchronize_session=False)

    db.commit()
    result = ensure_demo_admin(db)
    counts["users"] = int(bool(result["user_created"]))
    return counts
