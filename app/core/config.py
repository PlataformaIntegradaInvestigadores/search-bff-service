from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    V1_SEARCH_URL: str = "http://localhost:8001/api-se/v1/llm-search/semantic-search/"
    BASE_URL: str = "http://localhost:8001"
    DATASET_VERSION: str = "2026-04-us8"

    class Config:
        env_file = ".env"

settings = Settings()