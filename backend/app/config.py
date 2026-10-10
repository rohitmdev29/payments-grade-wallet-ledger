from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://wallet:wallet@localhost:5432/wallet"
    llm_provider: str = "mock"
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
