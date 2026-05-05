from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os, json

if os.getenv("DATABASE_URL"):
    db_url = os.getenv("DATABASE_URL")
else:
    secret = os.getenv("DB_MASTER_SECRET")
    if not secret:
        raise RuntimeError("Missing DB configuration. (Missing required env vars)")

    secret_json = json.loads(secret)
    username = secret_json["username"]
    password = secret_json["password"]
    host = os.getenv("DB_ENDPOINT")
    dbname = os.getenv("DB_NAME")

    if not host or not dbname:
        raise RuntimeError("Missing DB env vars")
    
    db_url = f"mysql+asyncmy://{username}:{password}@{host}:{port}/{dbname}"

engine = create_async_engine(db_url, echo=True, poolclass=NullPool)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session