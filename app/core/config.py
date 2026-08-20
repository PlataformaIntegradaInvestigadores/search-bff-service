from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    V1_SEARCH_URL: str = "http://localhost:8001/api-se/v1/llm-search/semantic-search/"
    V1_AUTHORS_URL: str = (
        "http://localhost:8001/api-se/v1/authors/authors/most_relevant_authors/"
    )
    V1_AUTHORS_FIND_URL: str = (
        "http://localhost:8001/api-se/v1/authors/authors/find_by_query/"
    )
    V1_AUTHORS_DETAIL_URL: str = "http://localhost:8001/api-se/v1/authors/authors/"
    V1_ARTICLES_RELEVANT_URL: str = (
        "http://localhost:8001/api-se/v1/articles/most-relevant-articles-by-topic/"
    )
    V1_ARTICLES_BY_AUTHOR_URL: str = (
        "http://localhost:8001/api-se/v1/articles/find-articles-by-author-id/"
    )
    V1_ARTICLES_DETAIL_URL: str = "http://localhost:8001/api-se/v1/articles/"
    BASE_URL: str = "http://localhost:8001"
    DATASET_VERSION: str = "2026-04-us8"

    class Config:
        env_file = ".env"


settings = Settings()
