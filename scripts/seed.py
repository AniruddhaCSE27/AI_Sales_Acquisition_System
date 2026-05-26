import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.seed import run_seed


def main() -> None:
    with SessionLocal() as db:
        counts = run_seed(db)
    print(f"Seed data ready: {counts}")


if __name__ == "__main__":
    main()
