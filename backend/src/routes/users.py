from typing import List

from fastapi import APIRouter, Depends

from src.schemas.user import UserReturnData
from src.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def get_users(
    service: UserService = Depends(UserService),
) -> List[UserReturnData]:
    return await service.get_all()


@router.get("/me")
def get_current_user() -> dict:
    return {"username": "Rick", "role": "admin"}
