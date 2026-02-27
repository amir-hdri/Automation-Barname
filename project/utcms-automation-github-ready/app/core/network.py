from typing import Any

RETRYABLE_NETWORK_MARKERS = (
    "timeout",
    "timed out",
    "readtimeout",
    "connecttimeout",
    "net::",
    "err_name_not_resolved",
    "name_not_resolved",
    "dns",
    "servfail",
    "could not resolve host",
    "temporary failure in name resolution",
    "nodename nor servname provided",
    "connection reset",
    "connection aborted",
    "connection refused",
    "connection closed",
    "connection terminated",
    "socket hang up",
    "target closed",
    "browser has been closed",
    "execution context was destroyed",
    # Additional markers for Iranian IP/Geoblocking issues
    "access denied",
    "403 forbidden",
    "connection timed out",
    "remote end closed connection",
    "failed to connect",
)


def is_retryable_network_error(error: Any) -> bool:
    """
    Check if the error is a temporary network issue that should be retried.
    Extended to cover common issues seen when accessing Iranian services.
    """
    message = str(error or "").lower()
    return any(marker in message for marker in RETRYABLE_NETWORK_MARKERS)
