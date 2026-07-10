from typing import Annotated, List

from fastapi import APIRouter, Depends, status

from src.dependencies.auth_dependency import get_current_user
from src.schemas.user import UserReturnData, UserVerifySchema
from src.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def get_users(
    service: UserService = Depends(UserService),
) -> List[UserReturnData]:
    return await service.get_all()


@router.get(path="/me", status_code=status.HTTP_200_OK, response_model=UserVerifySchema)
async def get_auth_user(
    user: Annotated[UserVerifySchema, Depends(get_current_user)],
) -> UserVerifySchema:
    return user
