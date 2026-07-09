from fastapi import Depends, HTTPException
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from src.db_dependency import DBDependency
from src.models import User
from src.schemas.user import CreateUser, UserReturnData


class UserManager:
    def __init__(self, db: DBDependency = Depends(DBDependency)) -> None:
        self.db = db
        self.model = User

    async def create_user(self, user: CreateUser) -> UserReturnData:
        async with self.db.db_session() as session:
            query = insert(self.model).values(**user.model_dump()).returning(self.model)

            try:
                result = await session.execute(query)
            except IntegrityError:
                raise HTTPException(status_code=400, detail="Cannot create new user!")

            await session.commit()

            user_data = result.scalar_one()
            return UserReturnData(**user_data.__dict__)
