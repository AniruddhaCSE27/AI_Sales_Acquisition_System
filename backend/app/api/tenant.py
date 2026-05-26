from fastapi import Request
from sqlalchemy.orm import Session

from app.models import Organization

DEFAULT_ORG_SLUG = "demo"


def resolve_tenant_slug(request: Request) -> str:
    explicit = request.headers.get("x-organization-slug")
    if explicit:
        return explicit.lower().strip()
    host = request.headers.get("host", "")
    first = host.split(":", 1)[0].split(".", 1)[0]
    if first and first not in {"localhost", "127", "api", "www"}:
        return first.lower()
    return DEFAULT_ORG_SLUG


def get_or_create_organization(db: Session, slug: str = DEFAULT_ORG_SLUG) -> Organization:
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if org:
        return org
    org = Organization(name="Demo Organization" if slug == DEFAULT_ORG_SLUG else slug.title(), slug=slug, primary_domain=None)
    db.add(org)
    db.flush()
    return org
