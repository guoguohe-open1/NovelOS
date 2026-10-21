import socket
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from novelos.api.main import create_app
from novelos.infrastructure.config import Settings


@pytest.fixture
def unavailable_database_settings() -> Iterator[Settings]:
    # Reserve a port without listening: connection attempts must fail locally.
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
        yield Settings(
            environment="test",
            database_url=SecretStr(f"postgresql+psycopg://test:test@127.0.0.1:{port}/test"),
            database_timeout_seconds=1,
        )


def test_database_outage_preserves_liveness_and_fails_readiness(
    unavailable_database_settings: Settings,
) -> None:
    with TestClient(create_app(unavailable_database_settings)) as client:
        live = client.get("/health/live")
        assert live.status_code == 200
        assert live.json() == {"status": "ok"}
        ready = client.get("/health/ready")
        assert ready.status_code == 503
        assert ready.json() == {"status": "not_ready"}
        assert "test:test" not in ready.text


def test_cors_allows_only_configured_origins(unavailable_database_settings: Settings) -> None:
    with TestClient(create_app(unavailable_database_settings)) as client:
        allowed = client.get("/health/live", headers={"Origin": "http://127.0.0.1:3000"})
        assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
        denied = client.get("/health/live", headers={"Origin": "https://example.invalid"})
        assert "access-control-allow-origin" not in denied.headers


def test_settings_read_environment_without_implicit_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text("NOVELOS_ENVIRONMENT=invalid\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVELOS_ENVIRONMENT", "test")
    assert Settings().environment == "test"
    monkeypatch.delenv("NOVELOS_ENVIRONMENT")
    assert Settings().environment == "development"


@pytest.mark.parametrize("url", ["sqlite:///test.db", "postgresql://host/db", "invalid"])
def test_settings_reject_unsupported_database_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        Settings(database_url=SecretStr(url))


@pytest.mark.parametrize("origin", ["*", "http://localhost:3000/", "https://host/path"])
def test_settings_reject_non_origins(origin: str) -> None:
    with pytest.raises(ValidationError):
        Settings(cors_origins=[origin])
