import os, json, ssl

from fastapi import Request
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

def create_db_engine():
    db_url = os.getenv("DATABASE_URL")
    connect_args = {}
    if not db_url:
        secret = json.loads(os.environ["DB_MASTER_SECRET"])
        db_url = f"mysql+asyncmy://{secret['username']}:{secret['password']}@{os.environ['DB_ENDPOINT']}/{os.environ['DB_NAME']}"
        connect_args = {"ssl": ssl.create_default_context(cafile=os.environ["DB_CA_BUNDLE"])}

    engine = create_async_engine(db_url, poolclass=NullPool, connect_args=connect_args)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    return engine, factory

async def get_session(request: Request):
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session
