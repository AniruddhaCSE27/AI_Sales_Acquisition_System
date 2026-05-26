import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.migrations import ensure_schema
from app.db.session import engine


def main() -> None:
    ensure_schema(engine)
    print("Database schema is ready.")


if __name__ == "__main__":
    main()
