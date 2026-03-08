"""Request logging middleware with correlation IDs."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status, and duration for every request.

    Attaches a correlation ID (X-Request-ID) to each response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id

        status = response.status_code
        log_msg = f"{request.method} {request.url.path} {status} {duration_ms:.1f}ms [{request_id}]"

        if status >= 500:
            logger.error(log_msg)
        elif status >= 400:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        return response
