from app.db.session import SessionLocal
from app.seed import run_seed


def main() -> None:
    with SessionLocal() as db:
        counts = run_seed(db)
    print(f"Seed data ready: {counts}")


if __name__ == "__main__":
    main()
