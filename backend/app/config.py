"""Application settings, read from environment variables and backend/.env."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "mock" needs no key or network; "gemini" calls the real LLM.
    ai_provider: str = "mock"

    # SecretStr so the key is masked in reprs, logs and tracebacks. Read it at the
    # point of use with .get_secret_value().
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.7-flash"

    database_path: str = "odin_tasks.db"


settings = Settings()
