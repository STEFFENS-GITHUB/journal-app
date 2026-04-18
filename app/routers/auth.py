from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.database.session import get_session, AsyncSessionLocal
from app.models.user import UserOut, User

security = HTTPBasic()
password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

async def get_current_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)], session: Annotated[AsyncSession, Depends(get_session)]):
    query = select(User).options(selectinload(User.journals)).where(User.username == credentials.username)
    result = await session.execute(query)
    user = result.scalars().first()
    if user and verify_password(credentials.password, user.password_hash):
        return UserOut.model_validate(user)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username or password is incorrect")

async def create_default_user():
    async with AsyncSessionLocal() as session:
        query = select(User).where(User.username == "default_user")
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            user = User(username="default_user", password_hash=hash_password("123"))
            session.add(user)
            await session.commit()