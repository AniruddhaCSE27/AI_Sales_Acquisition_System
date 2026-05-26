from app.db.migrations import ensure_schema
from app.db.session import engine


def main() -> None:
    ensure_schema(engine)
    print("Database schema is ready.")


if __name__ == "__main__":
    main()
