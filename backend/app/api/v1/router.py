from fastapi import APIRouter
from app.api.v1 import analytics, auth, calls, leads, manager_ai, operations, publishers, reports, users, websocket
from app.ws import telecaller_copilot

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(manager_ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(publishers.router, prefix="/publishers", tags=["publishers"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(telecaller_copilot.router, prefix="/ws", tags=["copilot"])
