from typing import Annotated

from fastapi import HTTPException, Depends
from starlette import status
from starlette.requests import Request

from src.schemas.user import UserVerifySchema
from src.managers.user import UserManager
from src.handlers.auth import AuthHandler


async def get_token_from_headers(request: Request) -> str:
    token = request.headers.get("Authorization")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing"
        )
    return token


async def get_current_user(
    token: Annotated[str, Depends(get_token_from_headers)],
    auth_handler: AuthHandler = Depends(AuthHandler),
    user_manager: UserManager = Depends(UserManager),
) -> UserVerifySchema:
    decoded_token = await auth_handler.decode_access_token(token=token)
    user_id = decoded_token.get("user_id")
    session_id = decoded_token.get("session_id")
    if not await user_manager.get_access_token(user_id=user_id, session_id=session_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid"
        )
    user = await user_manager.get_user_by_id(user_id=int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    user.session_id = session_id
    return user
