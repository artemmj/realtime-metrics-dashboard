from typing import List

from fastapi import Depends
from fastapi import HTTPException
from itsdangerous import BadSignature, URLSafeTimedSerializer

from src.tasks.send_email import send_confirmation_email
from src.handlers.auth import AuthHandler
from src.managers.user import UserManager
from src.schemas.user import RegisterUser, UserReturnData, CreateUser
from src.settings import settings


class UserService:
    def __init__(
        self,
        user_manager: UserManager = Depends(UserManager),
        auth_handler: AuthHandler = Depends(AuthHandler),
    ):
        self.user_manager = user_manager
        self.auth_handler = auth_handler
        self.serializer = URLSafeTimedSerializer(
            secret_key=settings.secret_key.get_secret_value()
        )

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
