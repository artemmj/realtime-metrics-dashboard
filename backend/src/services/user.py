from fastapi import Depends

from src.handlers.auth import AuthHandler
from src.managers.user import UserManager
from src.schemas.user import RegisterUser, UserReturnData, CreateUser


class UserService:
    def __init__(
        self,
        user_manager: UserManager = Depends(UserManager),
        auth_handler: AuthHandler = Depends(AuthHandler),
    ):
        self.user_manager = user_manager
        self.auth_handler = auth_handler

    async def register_user(self, user: RegisterUser) -> UserReturnData:
        hashed_password = await self.auth_handler.get_password_hash(user.password)
        new_user = CreateUser(email=user.email, hashed_password=hashed_password)
        return await self.user_manager.create_user(user=new_user)
