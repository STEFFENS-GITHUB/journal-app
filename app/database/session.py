from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os

if os.getenv("DOCKER_ENV") == 1:
    db_url = os.getenv("DATABASE_URL")
else:
    db_url="mysql+asyncmy://root:123@localhost:3306/test"

if not db_url:
    raise RuntimeError("db_url is not set")
engine = create_async_engine(db_url, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session