from typing import List

from fastapi import Depends, HTTPException
from sqlalchemy import insert, update, select
from sqlalchemy.exc import IntegrityError

from src.db_dependency import DBDependency
from src.models import User
from src.schemas.user import CreateUser, UserReturnData


class UserManager:
    def __init__(self, db: DBDependency = Depends(DBDependency)) -> None:
        self.db = db
        self.model = User

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
