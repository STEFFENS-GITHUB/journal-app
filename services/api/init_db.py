import asyncio
import os

from api.utils.database import create_db_engine
from api.main import validate_env, wait_db
from api.routers.auth import create_default_user

async def main():
    engine, session_factory = create_db_engine()
    await wait_db(engine)
    await create_default_user(session_factory)

if __name__ == "__main__":
    validate_env()
    for var in ("DEFAULT_USER", "DEFAULT_USER_PASSWORD"):
        if not os.getenv(var):
            raise RuntimeError(f"Missing {var} env var")
    asyncio.run(main())
