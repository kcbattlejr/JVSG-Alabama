"""Environment-backed settings shared by local and cloud execution."""

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project settings; integrations remain opt-in until configured."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    runtime_mode: Literal["local", "azure"] = Field(
        default="local",
        validation_alias="JVSG_RUNTIME_MODE",
    )
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:14b-instruct"
    azure_openai_endpoint: str | None = None
    azure_key_vault_url: str | None = None
    ms_graph_tenant_id: str | None = None
    ms_graph_client_id: str | None = None
    sid_hmac_secret: SecretStr | None = None


def get_settings() -> Settings:
    """Create settings from the process environment and optional .env file."""
    return Settings()
