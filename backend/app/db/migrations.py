from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

from app.db.session import Base

TENANT_COLUMNS = {
    "users": "organization_id",
    "publishers": "organization_id",
    "leads": "organization_id",
    "calls": "organization_id",
    "reports": "organization_id",
    "import_batches": "organization_id",
    "audit_logs": "organization_id",
    "model_training_runs": "organization_id",
    "vector_embeddings": "organization_id",
    "ai_jobs": "organization_id",
    "customer_memory": "organization_id",
    "knowledge_documents": "organization_id",
}

LEAD_COLUMNS = {
    "lead_notes": "TEXT",
    "next_best_action": "TEXT",
}

AI_CALL_SESSION_COLUMNS = {
    "simulation": "TEXT",
    "interest_level": "VARCHAR(40)",
    "sentiment": "VARCHAR(40)",
    "lead_score": "FLOAT DEFAULT 0",
    "objection": "VARCHAR(80)",
    "suggested_response": "TEXT",
    "next_action": "TEXT",
}


def ensure_schema(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    dialect = engine.dialect.name
    with engine.begin() as conn:
        for table, column in TENANT_COLUMNS.items():
            if not inspector.has_table(table):
                continue
            columns = {item["name"] for item in inspector.get_columns(table)}
            if column in columns:
                continue
            if dialect == "postgresql":
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} INTEGER"))
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_{column} ON {table} ({column})"))
            elif dialect == "sqlite":
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} INTEGER"))
        if inspector.has_table("calls"):
            columns = {item["name"] for item in inspector.get_columns("calls")}
            if "metadata_json" not in columns:
                if dialect == "postgresql":
                    conn.execute(text("ALTER TABLE calls ADD COLUMN IF NOT EXISTS metadata_json JSON DEFAULT '{}'"))
                elif dialect == "sqlite":
                    conn.execute(text("ALTER TABLE calls ADD COLUMN metadata_json JSON DEFAULT '{}'"))
        if inspector.has_table("leads"):
            columns = {item["name"] for item in inspector.get_columns("leads")}
            for column, column_type in LEAD_COLUMNS.items():
                if column not in columns:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE leads ADD COLUMN IF NOT EXISTS {column} {column_type}"))
                    elif dialect == "sqlite":
                        conn.execute(text(f"ALTER TABLE leads ADD COLUMN {column} {column_type}"))
        if inspector.has_table("ai_call_sessions"):
            columns = {item["name"] for item in inspector.get_columns("ai_call_sessions")}
            for column, column_type in AI_CALL_SESSION_COLUMNS.items():
                if column not in columns:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE ai_call_sessions ADD COLUMN IF NOT EXISTS {column} {column_type}"))
                    elif dialect == "sqlite":
                        conn.execute(text(f"ALTER TABLE ai_call_sessions ADD COLUMN {column} {column_type}"))
        if dialect == "postgresql":
            for value in ("admin", "agent"):
                conn.execute(text(f"ALTER TYPE role ADD VALUE IF NOT EXISTS '{value}'"))
            for value in ("interested", "counsellor_assigned", "rejected"):
                conn.execute(text(f"ALTER TYPE leadstatus ADD VALUE IF NOT EXISTS '{value}'"))
            for extension in ("pg_trgm", "vector"):
                try:
                    conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {extension}"))
                except SQLAlchemyError:
                    # Managed databases may not expose pgvector; the app keeps a
                    # JSON-vector fallback so boot should not be blocked.
                    pass
