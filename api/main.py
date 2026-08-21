from api.routers import journal, user, auth
from api.middleware.logging import LoggingMiddleware
from api.middleware.metrics import MetricsMiddleware
from api.utils.database import create_db_engine
from api.utils.queue import create_sqs_client
from api.utils.rate_limiter import RateLimiter
from fastapi import FastAPI, Request, HTTPException, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from contextlib import asynccontextmanager
import redis.asyncio as redis
import uvicorn
import asyncio
import os
from sqlalchemy import text

def validate_env():
    for var in ("JWT_SECRET_KEY", "REDIS_URL", "EMAIL_VERIFICATION_QUEUE_URL"):
        if not os.getenv(var):
            raise RuntimeError(f"Missing {var} env var")

    if not os.getenv("DATABASE_URL"):
        for var in ("DB_MASTER_SECRET", "DB_ENDPOINT", "DB_NAME"):
            if not os.getenv(var):
                raise RuntimeError(f"Missing {var} env var (required when DATABASE_URL is not set)")

async def wait_db(engine):
    for _ in range (30):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                break
        except Exception:
            await asyncio.sleep(2)
    else:
        raise RuntimeError("DB connection has failed.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_env()
    app.state.engine, app.state.session_factory = create_db_engine()
    app.state.sqs_client = create_sqs_client()
    app.state.redis_client = redis.from_url(os.getenv("REDIS_URL"), encoding="utf-8", decode_responses=True)

    await wait_db(app.state.engine)
    yield
    await app.state.redis_client.aclose()

app = FastAPI(lifespan=lifespan,
              dependencies=[Depends(RateLimiter(times=100, seconds=60, name="global"))])
app.add_middleware(LoggingMiddleware, exclude_paths={"/health", "/metrics"})
app.add_middleware(MetricsMiddleware)
app.include_router(journal.router)
app.include_router(user.router)
app.include_router(auth.router)

@app.get('/')
def index():
    return f"Welcome to the page"

@app.get("/health")
async def health(request: Request):
    checks = {}
    try:
        async with request.app.state.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    try:
        sqs_client = create_sqs_client(connect_timeout=1, read_timeout=1, max_attempts=0)
        await asyncio.to_thread(
            sqs_client.get_queue_attributes,
            QueueUrl=os.environ["EMAIL_VERIFICATION_QUEUE_URL"],
            AttributeNames=["QueueArn"],
        )
        checks["queue"] = "ok"
    except Exception:
        checks["queue"] = "unavailable"

    if checks["database"] == "ok":
        return {"status": "healthy", "checks": checks}
    raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": checks})

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000
    )