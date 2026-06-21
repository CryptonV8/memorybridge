from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    google_api_key: str = Field(default="")
    memorybridge_model: str = Field(default="gemini-2.5-pro")
    log_level: str = Field(default="INFO")
    otlp_endpoint: str = Field(default="")
    
    # Provider selection: "gemini" or "fake"
    agent_provider: str = Field(default="fake")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
