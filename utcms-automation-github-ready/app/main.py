import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends

from app.api.routes import reports, system, waybill_map
from app.automation.browser import browser_manager
from app.core.config import utcms_config
from app.core.database import init_db
from app.core.logging import configure_logging, reset_request_id, set_request_id
from app.core.security import require_sensitive_auth

configure_logging(utcms_config.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await browser_manager.initialize()
    yield
    await browser_manager.close()


app = FastAPI(
    title="سیستم اتوماسیون UTCMS",
    description="ربات هوشمند صدور بارنامه با قابلیت انتخاب مسیر و گزارش‌گیری",
    version="2.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = set_request_id(request_id)
    started = time.perf_counter()
    response = None

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "http_request_failed",
            extra={"extra_fields": {"method": request.method, "path": request.url.path}},
        )
        raise
    finally:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "http_request",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": elapsed_ms,
                    "client": request.client.host if request.client else None,
                }
            },
        )
        reset_request_id(token)

    if response is not None:
        response.headers["X-Request-ID"] = request_id
    return response


app.include_router(waybill_map.router)
app.include_router(reports.router)
app.include_router(system.router)


@app.get("/", tags=["وضعیت سیستم"], dependencies=[Depends(require_sensitive_auth)])
async def root():
    return {"message": "سیستم اتوماسیون UTCMS فعال است"}
