from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: str = ""

    # Database Configuration
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # JWT Configuration
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    GEMINI_API_KEY: Optional[str] = None

    DEEPSEEK_API_KEY: Optional[str] = None

    MILVUS_URI: Optional[str] = None
    MILVUS_TOKEN: Optional[str] = None
    MILVUS_COLLECTION_NAME: str = "product_embeddings"

    REDIS_URL: Optional[str] = None

    CELERY_BROKER_URL: Optional[str] = None

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
