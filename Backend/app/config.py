from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    APP_NAME: str = "Prepify"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "FastAPI + PostgreSQL with SQLAlchemy async"

    CORS_ORIGINS: list = ["*"]

    chroma_host: str
    chroma_port: int
    chroma_ssl: bool = False
    chroma_collection: str

    GROQ_API_KEY: str
    

    VAPI_ASSISTANT_ID: str = "your-vapi-assistant-id"
    VAPI_PRIVATE_KEY: str
    VAPI_PUBLIC_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()