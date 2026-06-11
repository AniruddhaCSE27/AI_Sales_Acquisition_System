from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LeadForge AI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 30
    database_url: str = "sqlite:///./sales_ai.db"
    redis_url: str = "redis://localhost:6379/0"
    require_redis_for_readiness: bool = False
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    rate_limit_requests: int = 120
    rate_limit_redis_prefix: str = "leadforge:rate_limit"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    deepgram_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_stream_path: str = "/api/v1/ws/twilio/media"
    twilio_max_retries: int = 3
    whisper_model: str = "whisper-1"
    model_registry_dir: str = "ai_models/registry"
    vector_db_dir: str = "ai_models/vector_db"
    rag_backend: str = "auto"
    sentry_dsn: str = ""
    otel_exporter_otlp_endpoint: str = ""
    public_base_url: str = "http://localhost:8000"
    reports_dir: str = "reports"
    uploads_dir: str = "uploads"
    cors_origins: list[str] = ["http://localhost:3000"]
    build_version: str = "local"
    seed_default_password: str = "Password123!"
    seed_demo_data: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
