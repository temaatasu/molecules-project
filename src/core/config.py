from pydantic_settings import BaseSettings, SettingsConfigDict
import logging


class Settings(BaseSettings):

    # Logging
    LOG_LEVEL: str = "INFO"

    # PostgreSQL
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def DATABASE_URL(self) -> str:
        """
        Asynchronously builds the full database URL.
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def CELERY_BROKER_URL(self) -> str:
        """
        Builds the Celery broker URL. (Using DB 1 for broker)
        """
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """
        Builds the Celery result backend URL. (Using DB 2 for results)
        """
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


try:
    settings = Settings()
except Exception as e:
    logging.error(f"Failed to load settings: {e}")
    raise
