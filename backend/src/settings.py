from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingModelConfigDefault:
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf8",
        extra="ignore",
    )


class DBSettings(BaseSettings, SettingModelConfigDefault):
    db_name: str = Field(default="postgres", alias="POSTGRES_NAME")
    db_user: str = Field(default="postgres", alias="POSTGRES_USER")
    db_password: SecretStr = Field(default="postgres", alias="POSTGRES_PASSWORD")
    db_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    db_port: int = Field(default=5432, alias="POSTGRES_PORT")
    db_echo: bool = Field(default=True, alias="POSTGRES_ECHO")

    @property
    def db_url(self):
        return (
            f"postgresql+asyncpg://{self.db_user}:"
            f"{self.db_password.get_secret_value()}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )


class EmailSettings(BaseSettings, SettingModelConfigDefault):
    email_host: str = Field(default="host", alias="EMAIL_HOST")
    email_port: int = Field(default=1111, alias="EMAIL_PORT")
    email_username: str = Field(default="username", alias="EMAIL_USERNAME")
    email_password: SecretStr = Field(default="pass", alias="EMAIL_PASSWORD")


class RedisSettings(BaseSettings, SettingModelConfigDefault):
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    @property
    def redis_url(self):
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class CelerySettings(BaseSettings, SettingModelConfigDefault):
    celery_broker_url: str = Field(
        default="redis://redis:6379/0", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://redis:6379/0", alias="CELERY_RESULT_BACKEND"
    )


class Settings(BaseSettings, SettingModelConfigDefault):
    secret_key: SecretStr = Field(default="", alias="SECRET_KEY")

    db_settings: DBSettings = DBSettings()
    email_settings: EmailSettings = EmailSettings()
    redis_settings: RedisSettings = RedisSettings()
    celery_settings: CelerySettings = CelerySettings()


settings = Settings()
