import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.automation.browser import browser_manager
from app.core.config import utcms_config
from app.core.database import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.get("/readyz")
async def readyz():
    checks = {
        "database": "unknown",
        "browser": "unknown",
        "config": "unknown",
    }

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        await browser_manager.initialize()
        checks["browser"] = "ok"
    except Exception:
        checks["browser"] = "error"

    try:
        valid_modes = {
            "api_key",
            "jwt",
            "api_key_or_jwt",
            "api_key_and_jwt",
            "off",
            "none",
            "disabled",
        }
        checks["config"] = (
            "ok" if utcms_config.API_AUTH_MODE in valid_modes else "error"
        )
    except Exception:
        checks["config"] = "error"

    ready = all(value == "ok" for value in checks.values())
    content = {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
    }

    if not ready:
        logger.warning("readiness_check_failed", extra={"extra_fields": content})

    return JSONResponse(status_code=200 if ready else 503, content=content)
