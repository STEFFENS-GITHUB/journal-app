from api.utils.database import get_session
from api.models.user import User, UserOut
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter
from api.routers.auth import get_current_user

router = APIRouter(prefix="/api/user")

@router.get('/{id}', response_model=UserOut)
async def get_user(user: Annotated[User, Depends(get_current_user)], id: int):
    if id != user.id:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete('/{id}', status_code=204)
async def delete_user(session: Annotated[AsyncSession, Depends(get_session)],
                  user: Annotated[User, Depends(get_current_user)],
                 id: int):
    if id != user.id:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    