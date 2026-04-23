from __future__ import annotations

import contextvars
import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_REQUEST_ID_HEADER = "X-Request-ID"
_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id_var.get()


def _normalize_request_id(value: str | None) -> str:
    normalized = (value or "").strip()
    return normalized or f"req_{uuid4().hex}"


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id()
        return True


_logging_configured = False


def configure_logging(level_name: str) -> None:
    global _logging_configured
    if _logging_configured:
        return

    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s",
    )

    root_logger = logging.getLogger()
    request_filter = RequestContextFilter()
    root_logger.addFilter(request_filter)
    for handler in root_logger.handlers:
        handler.addFilter(request_filter)

    _logging_configured = True


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, request_id_header_name: str = _REQUEST_ID_HEADER) -> None:
        super().__init__(app)
        self._request_id_header_name = request_id_header_name
        self._logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _normalize_request_id(request.headers.get(self._request_id_header_name))
        token = _request_id_var.set(request_id)
        request.state.request_id = request_id
        start = perf_counter()

        self._logger.info(
            "request_started",
            extra={
                "http_method": request.method,
                "path": request.url.path,
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((perf_counter() - start) * 1000, 2)
            self._logger.exception(
                "request_failed",
                extra={
                    "http_method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            _request_id_var.reset(token)
            raise

        duration_ms = round((perf_counter() - start) * 1000, 2)
        response.headers[self._request_id_header_name] = request_id
        self._logger.info(
            "request_completed",
            extra={
                "http_method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        _request_id_var.reset(token)
        return response


class InMemoryMetricsRegistry:
    """Dependency-free metrics skeleton for future expansion."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}

    def increment(self, name: str, amount: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + amount

    def snapshot(self) -> dict[str, int]:
        return dict(self._counters)


__all__ = [
    "InMemoryMetricsRegistry",
    "RequestContextFilter",
    "RequestLoggingMiddleware",
    "configure_logging",
    "get_request_id",
]
