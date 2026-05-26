import time
from collections import defaultdict, deque

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.migrations import ensure_schema
from app.db.session import engine
from app.health import ready, service_payload
from app.metrics import observe_request, prometheus_payload

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

RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_REQUESTS = 120
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    started = time.perf_counter()
    client = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _rate_buckets[client]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_REQUESTS and not request.url.path.startswith(("/health", "/live", "/ready", "/metrics")):
        return Response(content='{"detail":"Rate limit exceeded"}', status_code=429, media_type="application/json")
    bucket.append(now)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", method=request.method, path=request.url.path)
        raise
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    observe_request(request.method, request.url.path, response.status_code, elapsed_ms)
    logger.info("request_complete", method=request.method, path=request.url.path, status_code=response.status_code, elapsed_ms=elapsed_ms)
    return response


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
