import os
import time
from typing import Any

from redis import Redis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import SessionLocal

STARTED_AT = time.monotonic()


def uptime_seconds() -> float:
    return round(time.monotonic() - STARTED_AT, 3)


def check_database() -> dict[str, Any]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except SQLAlchemyError as exc:
        return {"status": "error", "error": exc.__class__.__name__}


def check_redis() -> dict[str, Any]:
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        client.close()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "error": exc.__class__.__name__}


def check_ai() -> dict[str, Any]:
    configured = bool(settings.openai_api_key)
    return {
        "status": "configured" if configured else "not_configured",
        "model": settings.openai_model,
        "required_for_startup": False,
    }


def check_twilio() -> dict[str, Any]:
    return {
        "status": "configured" if settings.twilio_account_sid and settings.twilio_phone_number else "demo_mode",
        "stream_path": settings.twilio_stream_path,
        "required_for_startup": False,
    }


def check_whisper() -> dict[str, Any]:
    return {"status": "configured" if settings.openai_api_key else "offline_fallback", "model": settings.whisper_model, "required_for_startup": False}


def check_vector_db() -> dict[str, Any]:
    return {"status": "ok", "path": settings.vector_db_dir}


def check_model_registry() -> dict[str, Any]:
    return {"status": "ok", "path": settings.model_registry_dir}


def dependency_status() -> dict[str, Any]:
    return {
        "database": check_database(),
        "redis": check_redis(),
        "openai": check_ai(),
        "twilio": check_twilio(),
        "whisper": check_whisper(),
        "vector_db": check_vector_db(),
        "model_registry": check_model_registry(),
        "tenant_middleware": {"status": "enabled"},
    }


def service_payload(status: str, include_environment: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "service": settings.app_name,
        "uptime": uptime_seconds(),
        "dependencies": dependency_status(),
        "build_version": settings.build_version,
    }
    if include_environment:
        payload["environment"] = {
            "name": settings.environment,
            "api_v1_prefix": settings.api_v1_prefix,
            "database_url": _redact_url(settings.database_url),
            "redis_url": _redact_url(settings.redis_url),
            "reports_dir": settings.reports_dir,
            "uploads_dir": settings.uploads_dir,
            "cwd": os.getcwd(),
        }
    return payload


def ready() -> tuple[bool, dict[str, Any]]:
    payload = service_payload("ok")
    required = (payload["dependencies"]["database"], payload["dependencies"]["redis"])
    ok = all(item["status"] == "ok" for item in required)
    payload["status"] = "ready" if ok else "not_ready"
    return ok, payload


def _redact_url(value: str) -> str:
    if "@" not in value or "://" not in value:
        return value
    scheme, rest = value.split("://", 1)
    return f"{scheme}://***@{rest.split('@', 1)[1]}"
