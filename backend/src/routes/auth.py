from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette import status

from src.dependencies.auth_dependency import get_current_user
from src.schemas.user import AuthUser, RegisterUser, UserReturnData, UserVerifySchema
from src.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserReturnData,
    status_code=status.HTTP_201_CREATED,
)
async def registration(
    user: RegisterUser, service: UserService = Depends(UserService)
) -> UserReturnData:
    return await service.register_user(user=user)


@router.get(path="/register_confirm", status_code=status.HTTP_200_OK)
async def confirm_registration(
    token: str, service: UserService = Depends(UserService)
) -> dict[str, str]:
    await service.confirm_user(token=token)
    return {"message": "Электронная почта подтверждена"}


@router.post(path="/login", status_code=status.HTTP_200_OK)
async def login(
    user: AuthUser, service: UserService = Depends(UserService)
) -> JSONResponse:
    return await service.login_user(user=user)


@router.get(path="/logout", status_code=status.HTTP_200_OK)
async def logout(
    user: Annotated[UserVerifySchema, Depends(get_current_user)],
    service: UserService = Depends(UserService),
) -> JSONResponse:
    return await service.logout_user(user=user)
