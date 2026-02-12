from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "HOM Backend"
    API_V1_STR: str = "/api/v1"

    # Database Settings - Added ': str' here
    DATABASE_URL: str = "mysql+pymysql://root:Manan35635%40@127.0.0.1:3306/hom_db"

    # Security Settings
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()