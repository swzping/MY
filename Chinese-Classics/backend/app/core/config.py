from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Chinese Classics Agent"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "chinese_classics"
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/chinese_classics"
    
    REDIS_URL: str = "redis://redis:6379/0"
    MILVUS_HOST: str = "milvus"
    MILVUS_PORT: int = 19530
    
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
