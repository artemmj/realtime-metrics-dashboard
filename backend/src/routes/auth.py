from fastapi import APIRouter, Depends
from starlette import status

from src.schemas.user import RegisterUser, UserReturnData
from src.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserReturnData,
    status_code=status.HTTP_201_CREATED,
)  
async def registration(
    user: RegisterUser,
    service: UserService = Depends(UserService)
) -> UserReturnData:
    return await service.register_user(user=user)
