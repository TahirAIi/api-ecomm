from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: str = os.getenv("BACKEND_CORS_ORIGINS", "")

    # Database Configuration
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    SQLALCHEMY_DATABASE_URI: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    FIRST_SUPERUSER: str = os.getenv("FIRST_SUPERUSER")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")

    MILVUS_URI: str = os.getenv("MILVUS_URI")
    MILVUS_TOKEN: str = os.getenv("MILVUS_TOKEN")
    MILVUS_COLLECTION_NAME: str = os.getenv(
        "MILVUS_COLLECTION_NAME", "product_embeddings"
    )

    REDIS_URL: str = os.getenv("REDIS_URL")

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")

    class Config:
        case_sensitive = True


settings = Settings()
