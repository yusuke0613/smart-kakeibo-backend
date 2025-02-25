from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Household Budget API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SCHEMA_NAME: str = "kakeibo"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "root"
    POSTGRES_SERVER: str = "localhost:5432"
    POSTGRES_DB: str = "postgres"
    DATABASE_URL: Optional[str] = None

    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATABASE_URL = "postgresql://postgres:root@localhost:5432/postgres"

settings = Settings() 