from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    APP_NAME: str = "VetOnlineCRM"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vetcrm.db")
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"


settings = Settings()
