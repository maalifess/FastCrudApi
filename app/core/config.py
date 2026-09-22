import os
import tempfile
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

env_name = os.getenv("ENVIRONMENT", "development")
env_file_name = f".env.{env_name}" if os.path.exists(f".env.{env_name}") else ".env"

class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    APP_TITLE: str = Field(default="FastCRUD MariaDB API")
    APP_VERSION: str = Field(default="2.1.0")

    ALLOWED_ORIGINS: List[str] = Field(default=["*"])

    DATABASE_URL: str = Field(default="")
    MARIADB_HOST: str = Field(default="")
    MARIADB_PORT: str = Field(default="3306")
    MARIADB_USER: str = Field(default="root")
    MARIADB_PASSWORD: str = Field(default="")
    MARIADB_DATABASE: str = Field(default="fast_crud_db")

    SECRET_KEY: str = Field(default="dev-secret-key-change-me")

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(default="dev-jwt-secret-change-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    model_config = SettingsConfigDict(
        env_file=env_file_name,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        if self.MARIADB_HOST or os.getenv("MARIADB_HOST"):
            host = self.MARIADB_HOST or os.getenv("MARIADB_HOST")
            user = self.MARIADB_USER or os.getenv("MARIADB_USER", "root")
            password = self.MARIADB_PASSWORD or os.getenv("MARIADB_PASSWORD", "")
            port = self.MARIADB_PORT or os.getenv("MARIADB_PORT", "3306")
            db_name = self.MARIADB_DATABASE or os.getenv("MARIADB_DATABASE", "fast_crud_db")
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

        # Production check: Fail fast if in production and no database config exists
        if self.ENVIRONMENT == "production":
            raise ValueError(
                "CRITICAL: Production environment requires DATABASE_URL or MARIADB_HOST to be explicitly set!"
            )

        db_file = os.path.join(tempfile.gettempdir(), "app_data.db")
        return f"sqlite:///{db_file}"

settings = Settings()
