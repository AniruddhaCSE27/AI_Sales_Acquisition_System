"""Safely create or repair the LeadForge local demo administrator."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.db.migrations import ensure_schema
from app.db.session import SessionLocal, engine
from app.core.config import settings
from app.seed import DEMO_PASSWORD, ensure_demo_admin


def main() -> None:
    ensure_schema(engine)
    with SessionLocal() as db:
        result = ensure_demo_admin(db)
    print(f"Demo admin ready (user_id={result['user_id']}).")
    print("Email: admin@demo.com")
    print(f"Password: {settings.seed_default_password or DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
