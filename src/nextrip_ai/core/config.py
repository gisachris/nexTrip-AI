from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str = "mock-key"
    PINECONE_API_KEY: str = "mock-key"
    PINECONE_INDEX_NAME: str = "nextrip-knowledge"

    class Config:
        env_file = ".env"

settings = Settings()
