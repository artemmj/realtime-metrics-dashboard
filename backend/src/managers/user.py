from typing import List

from fastapi import Depends, HTTPException
from sqlalchemy import insert, update, select
from sqlalchemy.exc import IntegrityError

from src.dependencies.redis_dependency import RedisDependency
from src.dependencies.db_dependency import DBDependency
from src.models import User
from src.schemas.user import (
    CreateUser,
    GetUserWithIDAndEmail,
    UserReturnData,
    UserVerifySchema,
)


class UserManager:
    def __init__(
        self,
        db: DBDependency = Depends(DBDependency),
        redis: RedisDependency = Depends(RedisDependency),
    ) -> None:
        self.db = db
        self.model = User
        self.redis = redis

    async def get_user_by_email(self, email: str) -> GetUserWithIDAndEmail | None:
        async with self.db.db_session() as session:
            query = select(
                self.model.id,
                self.model.email,
                self.model.hashed_password,
            ).where(self.model.email == email)
            result = await session.execute(query)
            user = result.mappings().first()
            if user:
                return GetUserWithIDAndEmail(**user)
            return None

    async def get_user_by_id(self, user_id: int) -> UserVerifySchema | None:
        async with self.db.db_session() as session:
            query = select(self.model.id, self.model.email).where(
                self.model.id == user_id
            )
            result = await session.execute(query)
            user = result.mappings().one_or_none()
            if user:
                return UserVerifySchema(**user)
            return None

    async def get_all(self) -> List[UserReturnData]:
        async with self.db.db_session() as session:
            query = select(self.model)
            result = await session.execute(query)
            users = result.scalars().all()
            return [UserReturnData.model_validate(user) for user in users]

    async def create(self, user: CreateUser) -> UserReturnData:
        async with self.db.db_session() as session:
            query = insert(self.model).values(**user.model_dump()).returning(self.model)

            try:
                result = await session.execute(query)
            except IntegrityError:
                raise HTTPException(status_code=400, detail="Cannot create new user!")

            await session.commit()

            user_data = result.scalar_one()
            return UserReturnData(**user_data.__dict__)

    async def confirm(self, email: str) -> None:
        async with self.db.db_session() as session:
            query = (
                update(self.model)
                .where(self.model.email == email)
                .values(is_verified=True, is_active=True)
            )
            await session.execute(query)
            await session.commit()

    async def get_access_token(self, user_id: int, session_id: str) -> str | None:
        async with self.redis.get_client() as client:
            return await client.get(f"{user_id}:{session_id}")

    async def revoke_access_token(self, user_id: int, session_id: str) -> None:
        async with self.redis.get_client() as client:
            await client.delete(f"{user_id}:{session_id}")
