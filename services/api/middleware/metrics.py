import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from api.utils.metrics import journal_request_duration_seconds, journal_requests_total

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        status_code = 500
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            route = request.scope.get("route")
            if route is not None:
                path = route.path
            elif "endpoint" in request.scope:
                path = request.url.path
            else:
                path = "unmatched"
            journal_requests_total.labels(method=request.method,route=path,status_code=status_code).inc()
            journal_request_duration_seconds.labels(method=request.method,route=path,status_code=status_code).observe(duration)
