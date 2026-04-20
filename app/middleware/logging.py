from datetime import datetime
from fastapi import Request 
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Callable
import uuid, logging, time, sys

class RequestLogData(BaseModel):
    timestamp: datetime
    request_id: str
    method: str
    path: str
    status_code: int
    process_time_ms: float
    client_ip: str | None = None
    user_agent: str

def default_log_handler(log_data: RequestLogData):
    logger = logging.getLogger("request_logger")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info(f"""
            Timestamp: {log_data.timestamp}
            Request ID: {log_data.request_id}
            Request Method: {log_data.method}
            Request Path: {log_data.path}
            Status Code: {log_data.status_code}
            Process Time: {log_data.process_time_ms}
            Source IP: {log_data.client_ip}
            Request Agent: {log_data.user_agent}
        """)

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_handler: Callable[[RequestLogData], None] | None = None):
        super().__init__(app)
        self.log_handler = log_handler or default_log_handler
        
        
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter_ns()
        response = await call_next(request)
        process_time = round((time.perf_counter_ns()-start_time)/1000000, 2)
        request_id = str(uuid.uuid4())

        response.headers["Process-Time-ms"] = str(process_time)
        response.headers["Request-ID"] = request_id
        log_data = RequestLogData(
            timestamp=datetime.now(),
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time_ms=process_time,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", None)
        )
        self.log_handler(log_data)
        return response