import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str


class GetUserByID(BaseModel):
    id: int


class GetUserByEmail(BaseModel):
    email: EmailStr


class RegisterUser(GetUserByEmail):
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


class AuthUser(GetUserByEmail):
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]


class CreateUser(GetUserByEmail):
    hashed_password: str


class GetUserWithIDAndEmail(GetUserByID, CreateUser):
    pass


class UserReturnData(GetUserByID, GetUserByEmail):
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
