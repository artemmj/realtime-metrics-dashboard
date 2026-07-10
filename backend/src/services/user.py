from typing import List

from fastapi import status, Depends
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer

from src.redis_dependency import RedisDependency
from src.tasks.send_email import send_confirmation_email
from src.handlers.auth import AuthHandler
from src.managers.user import UserManager
from src.schemas.user import (
    AuthUser,
    RegisterUser,
    UserReturnData,
    CreateUser,
    UserVerifySchema,
)
from src.settings import settings


class UserService:
    def __init__(
        self,
        user_manager: UserManager = Depends(UserManager),
        auth_handler: AuthHandler = Depends(AuthHandler),
        redis: RedisDependency = Depends(RedisDependency),
    ):
        self.user_manager = user_manager
        self.auth_handler = auth_handler
        self.serializer = URLSafeTimedSerializer(
            secret_key=settings.secret_key.get_secret_value()
        )
        self.redis = redis

    async def _store_access_token(
        self, token: str, user_id: int, session_id: str
    ) -> None:
        async with self.redis.get_client() as client:
            await client.set(f"{user_id}:{session_id}", token)

    async def get_all(self) -> List[UserReturnData]:
        return await self.user_manager.get_all()

    async def register_user(self, user: RegisterUser) -> UserReturnData:
        hashed_password = await self.auth_handler.get_password_hash(user.password)
        new_user = CreateUser(email=user.email, hashed_password=hashed_password)
        user_data = await self.user_manager.create(user=new_user)
        confirmation_token = self.serializer.dumps(user_data.email)
        send_confirmation_email.delay(
            to_email=user_data.email, token=confirmation_token
        )
        return user_data

    async def confirm_user(self, token: str) -> None:
        try:
            email = self.serializer.loads(token, max_age=3600)
        except BadSignature:
            raise HTTPException(status_code=400, detail="Bad token")
        await self.user_manager.confirm(email=email)

    async def login_user(self, user: AuthUser) -> JSONResponse:
        exist_user = await self.user_manager.get_user_by_email(email=user.email)
        if exist_user is None or not await self.auth_handler.verify_password(
            hashed_password=exist_user.hashed_password, raw_password=user.password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong email or password",
            )
        token, session_id = await self.auth_handler.create_access_token(
            user_id=exist_user.id
        )
        await self._store_access_token(
            token=token, user_id=exist_user.id, session_id=session_id
        )
        response = JSONResponse(
            content={"message": "Successfully access!", "token": token}
        )
        # response.set_cookie(
        #     key="Authorization",
        #     value=token,
        #     httponly=True,
        #     max_age=settings.access_token_expire,
        # )
        return response

    async def logout_user(self, user: UserVerifySchema) -> JSONResponse:
        await self.user_manager.revoke_access_token(
            user_id=user.id, session_id=user.session_id
        )
        response = JSONResponse(content={"message": "Logged out"})
        return response
