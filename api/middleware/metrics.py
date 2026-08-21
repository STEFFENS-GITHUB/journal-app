from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from api.utils.metrics import http_requests_total

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            if route is not None:
                path = route.path
            elif "endpoint" in request.scope:
                path = request.url.path
            else:
                path = "unmatched"
            http_requests_total.labels(
                method=request.method,
                path=path,
                status_code=status_code,
            ).inc()
