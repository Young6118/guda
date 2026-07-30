from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="GUDA_", extra="ignore")

    data_dir: Path = Field(default=Path("data"))
    database_path: Path = Field(default=Path("data/app.sqlite"))
    admin_username: str | None = Field(default=None)
    admin_password: str | None = Field(default=None)

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"
