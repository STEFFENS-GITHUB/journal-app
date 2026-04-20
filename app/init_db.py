import asyncio
from app.main import init_db

if __name__ == "__main__":
    asyncio.run(init_db())