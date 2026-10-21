from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    # Dotenv loading is explicit at the process boundary (uv run --env-file).
    model_config = SettingsConfigDict(
        env_prefix="NOVELOS_", env_file=None, extra="ignore", hide_input_in_errors=True
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://novelos:novelos_local_only@127.0.0.1:5432/novelos"
    )
    cors_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    database_timeout_seconds: int = Field(default=2, ge=1, le=30)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
            valid = url.drivername == "postgresql+psycopg" and bool(url.host and url.database)
        except Exception:
            valid = False
        if not valid:
            raise ValueError("A PostgreSQL psycopg URL with host and database is required")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, values: list[str]) -> list[str]:
        from urllib.parse import urlsplit

        for value in values:
            parsed = urlsplit(value)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in value
            ):
                raise ValueError("CORS origins must be explicit HTTP(S) origins without paths")
        return values
