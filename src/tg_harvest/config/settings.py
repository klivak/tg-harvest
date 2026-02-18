"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_id: int | None = None
    api_hash: str | None = None
    phone: str | None = None

    @field_validator("api_id", mode="before")
    @classmethod
    def empty_str_to_none_int(cls, v):
        if v == "" or v is None:
            return None
        return v

    @field_validator("api_hash", "phone", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

    session_name: str = "tg_harvest"
    flood_sleep_threshold: int = 60
    request_delay: float = 1.0
    output_dir: Path = Path("./output")
    web_port: int = 8777

    @property
    def session_path(self) -> Path:
        return Path("./sessions") / self.session_name

    @property
    def state_path(self) -> Path:
        return Path("./sessions") / "parse_state.json"
