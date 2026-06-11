import time
import uuid

import structlog
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.rate_limiter import too_many_requests
from app.db.migrations import ensure_schema
from app.db.session import engine
from app.health import ready, service_payload
from app.metrics import observe_request, prometheus_payload
from app.db.session import SessionLocal
from app.seed import ensure_demo_admin

configure_logging()
logger = structlog.get_logger(__name__)
ensure_schema(engine)

app = FastAPI(title=settings.app_name, version="1.0.0", openapi_url=f"{settings.api_v1_prefix}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def seed_local_demo_admin() -> None:
    if settings.seed_demo_data and settings.environment.lower() in {"development", "local", "test"}:
        with SessionLocal() as db:
            result = ensure_demo_admin(db)
        logger.info("demo_admin_ready", **result)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    client = request.client.host if request.client else "unknown"
    rate_key = f"{client}:{request.url.path}"
    if too_many_requests(rate_key) and not request.url.path.startswith(("/health", "/live", "/ready", "/metrics")):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", method=request.method, path=request.url.path, request_id=request_id)
        raise
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    observe_request(request.method, request.url.path, response.status_code, elapsed_ms)
    response.headers["X-Request-ID"] = request_id
    logger.info("request_complete", method=request.method, path=request.url.path, status_code=response.status_code, elapsed_ms=elapsed_ms, request_id=request_id)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "request_id": request_id}, headers={"X-Request-ID": request_id})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    logger.exception("unhandled_exception", method=request.method, path=request.url.path, request_id=request_id)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id}, headers={"X-Request-ID": request_id})


@app.get("/health")
def health() -> dict:
    return service_payload("ok")


@app.get("/live")
def live() -> dict[str, str]:
    return {"status": "alive", "service": settings.app_name}


@app.get("/ready")
def readiness(response: Response) -> dict:
    ok, payload = ready()
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload


@app.get("/debug/status")
def debug_status(response: Response) -> dict:
    ok, payload = ready()
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    payload.update(service_payload(payload["status"], include_environment=True))
    return payload


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=prometheus_payload(), media_type="text/plain; version=0.0.4")
