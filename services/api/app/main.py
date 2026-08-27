import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import auth, conversations, health, settings, users
from app.config.settings import get_settings
from app.observability.logging import RequestIdMiddleware, configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings_obj = get_settings()
app = FastAPI(title=settings_obj.app_name)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings_obj.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", extra={"request_id": getattr(request.state, "request_id", None)})
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": getattr(request.state, "request_id", None)})

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(settings.router)
