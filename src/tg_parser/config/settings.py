"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_id: int
    api_hash: str
    phone: str

    session_name: str = "tg_parser"
    flood_sleep_threshold: int = 60
    request_delay: float = 1.0
    output_dir: Path = Path("./output")

    @property
    def session_path(self) -> Path:
        return Path("./sessions") / self.session_name
