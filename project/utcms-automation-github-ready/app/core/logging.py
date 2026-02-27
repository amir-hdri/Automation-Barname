import contextvars
import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


def set_request_id(value: str):
    return request_id_ctx.set(value)


def reset_request_id(token) -> None:
    request_id_ctx.reset(token)


def get_request_id() -> str:
    return request_id_ctx.get()


def _sanitize_string(value: str) -> str:
    sanitized = value
    patterns = [
        (r"(?i)(authorization\s*[:=]\s*bearer\s+)[a-z0-9._\-]+", r"\1***"),
        (r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+", r"\1***"),
        (r"(?i)(jwt[_-]?secret\s*[:=]\s*)[^\s,;]+", r"\1***"),
        (r"(?i)(password\s*[:=]\s*)[^\s,;]+", r"\1***"),
        (r"(?i)(token\s*[:=]\s*)[^\s,;]+", r"\1***"),
    ]
    try:
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized)
    except Exception:
        # During interpreter teardown regex internals may already be unavailable.
        return value
    return sanitized


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, raw in value.items():
            lowered = str(key).lower()
            if any(
                secret_key in lowered
                for secret_key in (
                    "password",
                    "secret",
                    "token",
                    "api_key",
                    "authorization",
                )
            ):
                clean[key] = "***"
            else:
                clean[key] = sanitize(raw)
        return clean
    if isinstance(value, (list, tuple, set)):
        return [sanitize(v) for v in value]
    if isinstance(value, str):
        return _sanitize_string(value)
    return value


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize(record.getMessage()),
            "request_id": getattr(record, "request_id", get_request_id()),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            payload["extra"] = sanitize(extra_fields)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_level: str = "INFO") -> None:
    level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    formatter = JsonFormatter()
    request_filter = RequestIdFilter()

    # Reset handlers to avoid duplicate output during tests/reloads.
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(request_filter)
    root.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
