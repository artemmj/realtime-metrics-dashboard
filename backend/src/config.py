from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class DBSettings(BaseSettings):
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: SecretStr = "postgres"
    db_host: str = "localhost"
    db_port: int = 5432
    db_echo: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")

    @property
    def db_url(self):
        return (
            f"postgresql+asyncpg://{self.db_user}:"
            f"{self.db_password.get_secret_value()}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )


class Settings(BaseSettings):
    db_settings: DBSettings = DBSettings()


settings = Settings()


class DBDependency:
    def __init__(self) -> None:
        self._engine = create_async_engine(url=settings.db_settings.db_url, echo=settings.db_settings.db_echo)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autocommit=False,
        )

    @property
    def db_session(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory
