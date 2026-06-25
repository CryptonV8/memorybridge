from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    google_api_key: str = Field(default="")
    # gemini-2.5-flash: current recommended value for google-genai SDK 2.9.x / google-adk 2.3.x.
    # gemini-2.5-pro remains available (legacy, supported until at least Oct 2026).
    # Override via MEMORYBRIDGE_MODEL env var — not a secret, no need for Secret Manager.
    memorybridge_model: str = Field(default="gemini-2.5-flash")
    log_level: str = Field(default="INFO")
    otlp_endpoint: str = Field(default="")
    
    # Provider selection: "gemini" or "fake"
    agent_provider: str = Field(default="fake")

    # Demo Authentication Tokens
    demo_caregiver_token: str = Field(default="test-sentinel-cg-token")
    demo_assisted_user_token: str = Field(default="test-sentinel-au-token")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
