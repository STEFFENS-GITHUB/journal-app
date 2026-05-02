from app.database.session import engine, get_session
from app.models.base import Base
from app.routers.auth import create_default_user
from app.routers import journal, user
from app.middleware.logging import LoggingMiddleware
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
import uvicorn

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await create_default_user()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.include_router(journal.router)
app.include_router(user.router)

@app.get('/')
def index():
    return f"Welcome to the page"

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000
    )