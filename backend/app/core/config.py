from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    qdrant_url: str
    n8n_base_url: str
    openai_model: str = "gpt-4.1-mini"
    openai_api_key: str | None = None


settings = Settings()  # pyright: ignore[reportCallIssue]
